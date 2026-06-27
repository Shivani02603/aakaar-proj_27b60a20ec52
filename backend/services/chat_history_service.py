import uuid
from typing import List, Optional

from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from database.models import ChatSession, ChatMessage, User, Document
from database.config import get_db


class ChatHistoryService:
    @staticmethod
    def create_chat_session(user_id: uuid.UUID, document_id: uuid.UUID, title: str, db: Session = Depends(get_db)) -> ChatSession:
        try:
            # Validate user and document existence
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            document = db.query(Document).filter(Document.id == document_id).first()
            if not document:
                raise HTTPException(status_code=404, detail="Document not found")

            # Create new chat session
            chat_session = ChatSession(
                id=uuid.uuid4(),
                user_id=user_id,
                document_id=document_id,
                title=title,
                created_at=db.execute("SELECT NOW()").scalar(),
                updated_at=db.execute("SELECT NOW()").scalar(),
            )
            db.add(chat_session)
            db.commit()
            db.refresh(chat_session)
            return chat_session
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    @staticmethod
    def get_chat_session_by_id(session_id: uuid.UUID, db: Session = Depends(get_db)) -> ChatSession:
        try:
            chat_session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
            if not chat_session:
                raise HTTPException(status_code=404, detail="Chat session not found")
            return chat_session
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    @staticmethod
    def list_chat_sessions(user_id: uuid.UUID, db: Session = Depends(get_db)) -> List[ChatSession]:
        try:
            chat_sessions = db.query(ChatSession).filter(ChatSession.user_id == user_id).all()
            return chat_sessions
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    @staticmethod
    def update_chat_session(session_id: uuid.UUID, title: Optional[str], db: Session = Depends(get_db)) -> ChatSession:
        try:
            chat_session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
            if not chat_session:
                raise HTTPException(status_code=404, detail="Chat session not found")

            if title:
                chat_session.title = title
                chat_session.updated_at = db.execute("SELECT NOW()").scalar()

            db.commit()
            db.refresh(chat_session)
            return chat_session
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    @staticmethod
    def delete_chat_session(session_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
        try:
            chat_session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
            if not chat_session:
                raise HTTPException(status_code=404, detail="Chat session not found")

            db.delete(chat_session)
            db.commit()
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    @staticmethod
    def create_chat_message(session_id: uuid.UUID, role: str, content: str, chunk_ids: Optional[List[uuid.UUID]], db: Session = Depends(get_db)) -> ChatMessage:
        try:
            # Validate chat session existence
            chat_session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
            if not chat_session:
                raise HTTPException(status_code=404, detail="Chat session not found")

            # Create new chat message
            chat_message = ChatMessage(
                id=uuid.uuid4(),
                session_id=session_id,
                role=role,
                content=content,
                chunk_ids=chunk_ids,
                created_at=db.execute("SELECT NOW()").scalar(),
            )
            db.add(chat_message)
            db.commit()
            db.refresh(chat_message)
            return chat_message
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    @staticmethod
    def get_chat_messages_by_session(session_id: uuid.UUID, db: Session = Depends(get_db)) -> List[ChatMessage]:
        try:
            chat_messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).all()
            if not chat_messages:
                raise HTTPException(status_code=404, detail="No messages found for this session")
            return chat_messages
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    @staticmethod
    def delete_chat_message(message_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
        try:
            chat_message = db.query(ChatMessage).filter(ChatMessage.id == message_id).first()
            if not chat_message:
                raise HTTPException(status_code=404, detail="Chat message not found")

            db.delete(chat_message)
            db.commit()
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")