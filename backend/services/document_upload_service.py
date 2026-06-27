import os
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException, UploadFile, Depends
from sqlalchemy.orm import Session
from database.models import Document, User
from database.config import get_db


class DocumentUploadService:
    def __init__(self, db: Session):
        self.db = db

    def create_document(self, user_id: uuid.UUID, file: UploadFile) -> Document:
        # Validate file type
        if file.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

        # Generate file path and save the file
        file_extension = os.path.splitext(file.filename)[1]
        if file_extension.lower() != ".pdf":
            raise HTTPException(status_code=400, detail="Invalid file extension. Only .pdf files are allowed.")

        file_id = uuid.uuid4()
        file_path = f"uploads/{file_id}{file_extension}"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "wb") as f:
            f.write(file.file.read())

        # Create document record
        document = Document(
            id=file_id,
            user_id=user_id,
            filename=file.filename,
            file_path=file_path,
            file_size=os.path.getsize(file_path),
            status="uploaded",
            uploaded_at=datetime.utcnow(),
            processed_at=None,
        )
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)

        return document

    def get_document_by_id(self, document_id: uuid.UUID) -> Document:
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found.")
        return document

    def list_documents(self, user_id: uuid.UUID) -> List[Document]:
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
        try:
            os.remove(document.file_path)
        except FileNotFoundError:
            pass  # File might already be deleted

        self.db.delete(document)
        self.db.commit()


# Dependency function to get the service instance
def get_document_upload_service(db: Session = Depends(get_db)) -> DocumentUploadService:
    return DocumentUploadService(db)