from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from pydantic import BaseModel, Field
from database.models import Document, User
from database.config import get_db
from backend.services.auth import get_current_user

router = APIRouter(tags=["Document Upload"])

# Pydantic Schemas
class DocumentBase(BaseModel):
    id: UUID
    user_id: UUID
    filename: str
    file_path: str
    file_size: int
    status: str
    uploaded_at: str
    processed_at: str | None

    class Config:
        from_attributes = True

class DocumentResponse(DocumentBase):
    pass

class DocumentUploadResponse(BaseModel):
    id: UUID
    filename: str
    status: str

    class Config:
        from_attributes = True

# Helper functions
async def save_uploaded_file(file: UploadFile, user_id: UUID, db: Session) -> Document:
    file_path = f"/uploads/{user_id}/{file.filename}"
    file_size = len(await file.read())
    document = Document(
        user_id=user_id,
        filename=file.filename,
        file_path=file_path,
        file_size=file_size,
        status="uploaded",
        uploaded_at="now",  # Replace with actual timestamp logic
        processed_at=None,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document

def list_user_documents(user_id: UUID, db: Session) -> List[Document]:
    return db.query(Document).filter(Document.user_id == user_id).all()

# Routes
@router.post("/documents/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Endpoint to upload a document. Only authenticated users can upload.
    """
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed."
        )

    try:
        document = await save_uploaded_file(file, current_user.id, db)
        return DocumentUploadResponse(
            id=document.id,
            filename=document.filename,
            status=document.status,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while uploading the document."
        )

@router.get("/documents", response_model=List[DocumentResponse], status_code=status.HTTP_200_OK)
async def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Endpoint to list all documents uploaded by the authenticated user.
    """
    try:
        documents = list_user_documents(current_user.id, db)
        return documents
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching documents."
        )