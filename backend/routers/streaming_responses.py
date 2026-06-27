from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import AsyncGenerator
from uuid import UUID
from pydantic import BaseModel, Field
from database.models import ChatSession, ChatMessage
from database.config import get_db
from backend.services.auth import get_current_user

router = APIRouter(tags=["Streaming Responses"])

class StreamAnswerRequest(BaseModel):
    session_id: UUID
    query: str

class StreamAnswerResponse(BaseModel):
    role: str = Field(..., description="Role of the message sender")
    content: str = Field(..., description="Content of the message")

async def generate_streaming_answer(query: str, session_id: UUID) -> AsyncGenerator[str, None]:
    """
    Mock implementation of the streaming answer generator.
    Replace this with actual logic as needed.
    """
    for token in ["This ", "is ", "a ", "mock ", "response."]:
        yield token

@router.get("/stream/answer", response_model=StreamAnswerResponse)
async def stream_answer(
    request: StreamAnswerRequest,
    db: Session = Depends(get_db),
    current_user: UUID = Depends(get_current_user),
) -> StreamingResponse:
    """
    Streams the answer tokens to the frontend in real-time.
    """
    # Validate session existence
    session = db.query(ChatSession).filter(ChatSession.id == request.session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    if session.user_id != current_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this chat session"
        )

    async def answer_stream() -> AsyncGenerator[str, None]:
        try:
            async for token in generate_streaming_answer(request.query, session.id):
                yield token
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error generating streaming answer: {str(e)}"
            )

    return StreamingResponse(answer_stream(), media_type="text/plain")