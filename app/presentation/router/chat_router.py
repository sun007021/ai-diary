from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.usecase.send_message import SendMessageUseCase
from app.application.usecase.start_chat_session import StartChatSessionUseCase
from app.infrastructure.config.database import get_db
from app.infrastructure.external.clova_client import ClovaClient
from app.infrastructure.persistence.chat_session_repository_impl import ChatSessionRepositoryImpl
from app.presentation.router.schemas import (
    ChatMessageResponse,
    ChatSessionResponse,
    SendMessageRequest,
    SendMessageResponse,
)

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


def _get_session_response(session) -> ChatSessionResponse:
    return ChatSessionResponse(
        id=session.id,
        session_date=session.session_date,
        messages=[
            ChatMessageResponse(role=m.role, content=m.content, created_at=m.created_at)
            for m in session.messages
        ],
        is_finalized=session.is_finalized,
        user_message_count=session.user_message_count,
        should_suggest_finalize=session.should_suggest_finalize,
        created_at=session.created_at,
    )


@router.post("/sessions", response_model=ChatSessionResponse)
async def start_session(db: AsyncSession = Depends(get_db)):
    repo = ChatSessionRepositoryImpl(db)
    ai = ClovaClient()
    usecase = StartChatSessionUseCase(repo, ai)
    session = await usecase.execute()
    return _get_session_response(session)


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_session(session_id: UUID, db: AsyncSession = Depends(get_db)):
    repo = ChatSessionRepositoryImpl(db)
    session = await repo.find_by_id(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
    return _get_session_response(session)


@router.post("/sessions/{session_id}/messages", response_model=SendMessageResponse)
async def send_message(session_id: UUID, body: SendMessageRequest, db: AsyncSession = Depends(get_db)):
    repo = ChatSessionRepositoryImpl(db)
    ai = ClovaClient()
    usecase = SendMessageUseCase(repo, ai)
    try:
        user_msg, ai_msg, suggest = await usecase.execute(session_id, body.content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return SendMessageResponse(
        user_message=ChatMessageResponse(role=user_msg.role, content=user_msg.content, created_at=user_msg.created_at),
        ai_message=ChatMessageResponse(role=ai_msg.role, content=ai_msg.content, created_at=ai_msg.created_at),
        should_suggest_finalize=suggest,
    )
