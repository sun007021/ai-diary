from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.service.ai_chat_service import AiChatService
from app.domain.repository.chat_session_repository import ChatSessionRepository
from app.domain.repository.diary_repository import DiaryRepository
from app.infrastructure.config.database import get_db
from app.infrastructure.external.clova_client import ClovaClient
from app.infrastructure.persistence.chat_session_repository_impl import ChatSessionRepositoryImpl
from app.infrastructure.persistence.diary_repository_impl import DiaryRepositoryImpl


def get_chat_session_repo(db: AsyncSession = Depends(get_db)) -> ChatSessionRepository:
    return ChatSessionRepositoryImpl(db)


def get_diary_repo(db: AsyncSession = Depends(get_db)) -> DiaryRepository:
    return DiaryRepositoryImpl(db)


def get_ai_chat_service() -> AiChatService:
    return ClovaClient()