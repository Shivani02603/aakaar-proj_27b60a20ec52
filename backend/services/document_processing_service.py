import os
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from PyPDF2 import PdfReader
from openai import Embedding
from database.models import Document, DocumentChunk
from database.config import get_db


class DocumentProcessingService:
    def __init__(self, db: Session):
        self.db = db

    def create_document(self, user_id: uuid.UUID, filename: str, file_path: str, file_size: int) -> Document:
        document = Document(
            id=uuid.uuid4(),
            user_id=user_id,
            filename=filename,
            file_path=file_path,
            file_size=file_size,
            status="uploaded",
            uploaded_at=datetime.utcnow(),
            processed_at=None
        )
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document

    def get_document_by_id(self, document_id: uuid.UUID) -> Document:
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return document

    def list_all_documents(self, user_id: uuid.UUID) -> List[Document]:
        documents = self.db.query(Document).filter(Document.user_id == user_id).all()
        return documents

    def update_document_status(self, document_id: uuid.UUID, status: str) -> Document:
        document = self.get_document_by_id(document_id)
        document.status = status
        document.processed_at = datetime.utcnow() if status == "processed" else None
        self.db.commit()
        self.db.refresh(document)
        return document

    def delete_document(self, document_id: uuid.UUID) -> None:
        document = self.get_document_by_id(document_id)
        self.db.delete(document)
        self.db.commit()

    def process_document(self, document_id: uuid.UUID) -> List[DocumentChunk]:
        document = self.get_document_by_id(document_id)
        if document.status != "uploaded":
            raise HTTPException(status_code=400, detail="Document is not in uploaded state")

        # Extract text from PDF
        try:
            reader = PdfReader(document.file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to extract text from PDF: {str(e)}")

        # Split text into chunks
        chunks = self._split_text_into_chunks(text)

        # Generate embeddings and save chunks
        document_chunks = []
        for index, chunk in enumerate(chunks):
            embedding = self._generate_embedding(chunk)
            document_chunk = DocumentChunk(
                id=uuid.uuid4(),
                document_id=document.id,
                chunk_index=index,
                content=chunk,
                embedding=embedding,
                metadata={},
                created_at=datetime.utcnow()
            )
            self.db.add(document_chunk)
            document_chunks.append(document_chunk)

        self.db.commit()
        self.update_document_status(document.id, "processed")
        return document_chunks

    def _split_text_into_chunks(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        tokens = text.split()
        chunks = []
        start = 0
        while start < len(tokens):
            end = min(start + chunk_size, len(tokens))
            chunk = " ".join(tokens[start:end])
            chunks.append(chunk)
            start += chunk_size - overlap
        return chunks

    def _generate_embedding(self, text: str) -> List[float]:
        try:
            embedding_model = Embedding(model="text-embedding-3-small")
            embedding = embedding_model.embed(text)
            return embedding
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate embedding: {str(e)}")