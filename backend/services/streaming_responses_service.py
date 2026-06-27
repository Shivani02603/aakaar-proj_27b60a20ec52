import uuid
from typing import List, Optional

from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from database.models import ChatMessage, ChatSession
from database.config import get_db


class StreamingResponsesService:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def create_chat_message(self, session_id: uuid.UUID, role: str, content: str, chunk_ids: Optional[List[uuid.UUID]] = None) -> ChatMessage:
        try:
            chat_session = self.db.query(ChatSession).filter(ChatSession.id == session_id).first()
            if not chat_session:
                raise HTTPException(status_code=404, detail="Chat session not found")

            new_message = ChatMessage(
                id=uuid.uuid4(),
                session_id=session_id,
                role=role,
                content=content,
                chunk_ids=chunk_ids or [],
                created_at=datetime.utcnow()
            )
            self.db.add(new_message)
            self.db.commit()
            self.db.refresh(new_message)
            return new_message
        except SQLAlchemyError as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail="Failed to create chat message") from e

    def get_chat_message_by_id(self, message_id: uuid.UUID) -> ChatMessage:
        try:
            message = self.db.query(ChatMessage).filter(ChatMessage.id == message_id).first()
            if not message:
                raise HTTPException(status_code=404, detail="Chat message not found")
            return message
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail="Failed to retrieve chat message") from e

    def list_all_chat_messages(self, session_id: uuid.UUID) -> List[ChatMessage]:
        try:
            messages = self.db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at).all()
            if not messages:
                raise HTTPException(status_code=404, detail="No chat messages found for the session")
            return messages
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail="Failed to list chat messages") from e

    def update_chat_message(self, message_id: uuid.UUID, content: Optional[str] = None, chunk_ids: Optional[List[uuid.UUID]] = None) -> ChatMessage:
        try:
            message = self.db.query(ChatMessage).filter(ChatMessage.id == message_id).first()
            if not message:
                raise HTTPException(status_code=404, detail="Chat message not found")

            if content is not None:
                message.content = content
            if chunk_ids is not None:
                message.chunk_ids = chunk_ids

            self.db.commit()
            self.db.refresh(message)
            return message
        except SQLAlchemyError as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail="Failed to update chat message") from e

    def delete_chat_message(self, message_id: uuid.UUID) -> None:
        try:
            message = self.db.query(ChatMessage).filter(ChatMessage.id == message_id).first()
            if not message:
                raise HTTPException(status_code=404, detail="Chat message not found")

            self.db.delete(message)
            self.db.commit()
        except SQLAlchemyError as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail="Failed to delete chat message") from e

    def stream_answer(self, session_id: uuid.UUID, answer_generator) -> None:
        """
        Streams answer tokens to the frontend in real-time.
        :param session_id: UUID of the chat session
        :param answer_generator: Generator yielding answer tokens
        """
        try:
            chat_session = self.db.query(ChatSession).filter(ChatSession.id == session_id).first()
            if not chat_session:
                raise HTTPException(status_code=404, detail="Chat session not found")

            for token in answer_generator:
                # Simulate streaming by yielding tokens
                yield {"token": token, "status": "typing"}
        except Exception as e:
            raise HTTPException(status_code=500, detail="Failed to stream answer") from e