from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ChatMessageResponse(BaseModel):
    role: str
    content: str
    created_at: datetime


class ChatSessionResponse(BaseModel):
    id: UUID
    session_date: date
    messages: list[ChatMessageResponse]
    is_finalized: bool
    user_message_count: int
    should_suggest_finalize: bool
    created_at: datetime


class SendMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)


class SendMessageResponse(BaseModel):
    user_message: ChatMessageResponse
    ai_message: ChatMessageResponse
    should_suggest_finalize: bool


class DiaryResponse(BaseModel):
    id: UUID
    diary_date: date
    title: str
    content: str
    emotion: str
    satisfaction: int
    chat_session_id: UUID | None
    created_at: datetime


class DiaryListResponse(BaseModel):
    items: list[DiaryResponse]
    total: int
