from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.service.ai_chat_service import AiChatService
from app.application.service.embedding_service import EmbeddingService
from app.application.usecase.chat_agent import ChatAgent
from app.application.usecase.extract_chunks import ExtractChunksUseCase
from app.domain.repository.chat_session_repository import ChatSessionRepository
from app.domain.repository.diary_repository import DiaryRepository
from app.domain.repository.event_chunk_repository import EventChunkRepository
from app.infrastructure.config.database import get_db
from app.infrastructure.external.clova_client import ClovaClient
from app.infrastructure.external.embedding_service_impl import SentenceTransformerEmbeddingService
from app.infrastructure.persistence.chat_session_repository_impl import ChatSessionRepositoryImpl
from app.infrastructure.persistence.diary_repository_impl import DiaryRepositoryImpl
from app.infrastructure.persistence.event_chunk_repository_impl import EventChunkRepositoryImpl

_embedding_service: EmbeddingService | None = None


def get_chat_session_repo(db: AsyncSession = Depends(get_db)) -> ChatSessionRepository:
    return ChatSessionRepositoryImpl(db)


def get_diary_repo(db: AsyncSession = Depends(get_db)) -> DiaryRepository:
    return DiaryRepositoryImpl(db)


def get_event_chunk_repo(db: AsyncSession = Depends(get_db)) -> EventChunkRepository:
    return EventChunkRepositoryImpl(db)


def get_ai_chat_service() -> AiChatService:
    return ClovaClient()


def get_embedding_service() -> EmbeddingService:
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = SentenceTransformerEmbeddingService()
    return _embedding_service


def get_extract_chunks_usecase(
    ai: AiChatService = Depends(get_ai_chat_service),
    embedding: EmbeddingService = Depends(get_embedding_service),
    event_chunk_repo: EventChunkRepository = Depends(get_event_chunk_repo),
) -> ExtractChunksUseCase:
    return ExtractChunksUseCase(ai, embedding, event_chunk_repo)


def get_chat_agent(
    ai: AiChatService = Depends(get_ai_chat_service),
    embedding: EmbeddingService = Depends(get_embedding_service),
    event_chunk_repo: EventChunkRepository = Depends(get_event_chunk_repo),
) -> ChatAgent:
    return ChatAgent(ai, embedding, event_chunk_repo)
