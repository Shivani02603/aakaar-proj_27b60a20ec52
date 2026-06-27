from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from pydantic import BaseModel, Field
from database.models import Document, DocumentChunk, User
from database.config import get_db
from backend.services.auth import get_current_user

router = APIRouter(tags=["Document Processing"])

# Pydantic Schemas
class DocumentBase(BaseModel):
    id: UUID
    user_id: UUID
    filename: str
    file_path: str
    file_size: int
    status: str
    uploaded_at: str
    processed_at: str

class DocumentResponse(DocumentBase):
    pass

class DocumentChunkBase(BaseModel):
    id: UUID
    document_id: UUID
    chunk_index: int
    content: str
    metadata: dict
    created_at: str

class DocumentChunkResponse(DocumentChunkBase):
    pass

# Helper functions
async def process_pdf(file: UploadFile, user_id: UUID, db: Session) -> Document:
    """
    Process the uploaded PDF file: save it and create a Document entry.
    """
    file_path = f"/uploads/{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    document = Document(
        user_id=user_id,
        filename=file.filename,
        file_path=file_path,
        file_size=len(file.file),
        status="processed",
        uploaded_at="now()",  # Replace with actual timestamp logic
        processed_at="now()",  # Replace with actual timestamp logic
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document

async def generate_embeddings(document_id: UUID, db: Session):
    """
    Generate embeddings for the document chunks.
    """
    chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).all()
    for chunk in chunks:
        chunk.embedding = [0.0] * 512  # Replace with actual embedding logic
        db.add(chunk)
    db.commit()

# Routes
@router.post("/documents/process", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def process_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Process an uploaded PDF file: extract text, split into chunks, and generate embeddings.
    """
    try:
        # Save the uploaded file
        document = await process_pdf(file, current_user.id, db)

        # Generate embeddings for the document chunks
        await generate_embeddings(document.id, db)

        return document
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing document: {str(e)}",
        )

@router.get("/documents", response_model=List[DocumentResponse], status_code=status.HTTP_200_OK)
async def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all documents for the current user.
    """
    documents = db.query(Document).filter(Document.user_id == current_user.id).all()
    return documents

@router.get("/documents/{document_id}", response_model=DocumentResponse, status_code=status.HTTP_200_OK)
async def get_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve a specific document by ID.
    """
    document = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    return document

@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a specific document by ID.
    """
    document = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    db.delete(document)
    db.commit()
    return {"detail": "Document deleted successfully"}

@router.get("/documents/{document_id}/chunks", response_model=List[DocumentChunkResponse], status_code=status.HTTP_200_OK)
async def list_document_chunks(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all chunks for a specific document.
    """
    document = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).all()
    return chunks