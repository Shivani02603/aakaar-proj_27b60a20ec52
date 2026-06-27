import uuid
from typing import List, Dict, Optional

from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from openai import ChatCompletion
from database.models import DocumentChunk, ChatMessage
from database.config import get_db


class QuestionAnsweringService:
    def __init__(self, db: Session):
        self.db = db

    def create_chat_message(self, session_id: uuid.UUID, role: str, content: str, chunk_ids: List[uuid.UUID]) -> ChatMessage:
        try:
            chat_message = ChatMessage(
                id=uuid.uuid4(),
                session_id=session_id,
                role=role,
                content=content,
                chunk_ids=chunk_ids,
                created_at=datetime.utcnow()
            )
            self.db.add(chat_message)
            self.db.commit()
            self.db.refresh(chat_message)
            return chat_message
        except SQLAlchemyError as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    def get_chat_message_by_id(self, message_id: uuid.UUID) -> ChatMessage:
        chat_message = self.db.query(ChatMessage).filter(ChatMessage.id == message_id).first()
        if not chat_message:
            raise HTTPException(status_code=404, detail="Chat message not found")
        return chat_message

    def list_all_chat_messages(self, session_id: uuid.UUID) -> List[ChatMessage]:
        chat_messages = self.db.query(ChatMessage).filter(ChatMessage.session_id == session_id).all()
        return chat_messages

    def update_chat_message(self, message_id: uuid.UUID, content: Optional[str] = None) -> ChatMessage:
        chat_message = self.get_chat_message_by_id(message_id)
        if content:
            chat_message.content = content
        try:
            self.db.commit()
            self.db.refresh(chat_message)
            return chat_message
        except SQLAlchemyError as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    def delete_chat_message(self, message_id: uuid.UUID) -> None:
        chat_message = self.get_chat_message_by_id(message_id)
        try:
            self.db.delete(chat_message)
            self.db.commit()
        except SQLAlchemyError as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    def generate_answer(self, query: str, top_k: int = 5) -> Dict[str, str]:
        try:
            # Retrieve top-k relevant chunks based on embeddings
            chunks = self.db.query(DocumentChunk).order_by(DocumentChunk.embedding.distance(query)).limit(top_k).all()
            if not chunks:
                raise HTTPException(status_code=404, detail="No relevant chunks found")

            # Prepare context for LLM
            context = "\n".join([f"Chunk {chunk.chunk_index}: {chunk.content}" for chunk in chunks])

            # Generate answer using LLM
            llm_response = ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": f"Answer the following question concisely with citations:\n\n{query}\n\nContext:\n{context}"}
                ]
            )
            answer = llm_response.choices[0].message["content"]

            # Format citations
            citations = {f"Chunk {chunk.chunk_index}": chunk.metadata for chunk in chunks}

            return {"answer": answer, "citations": citations}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error generating answer: {str(e)}")