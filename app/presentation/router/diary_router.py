from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.usecase.finalize_diary import FinalizeDiaryUseCase
from app.infrastructure.config.database import get_db
from app.infrastructure.external.clova_client import ClovaClient
from app.infrastructure.persistence.chat_session_repository_impl import ChatSessionRepositoryImpl
from app.infrastructure.persistence.diary_repository_impl import DiaryRepositoryImpl
from app.presentation.router.schemas import DiaryResponse

router = APIRouter(prefix="/api/v1/diaries", tags=["diaries"])


@router.post("/{session_id}/finalize", response_model=DiaryResponse)
async def finalize_diary(session_id: UUID, db: AsyncSession = Depends(get_db)):
    chat_repo = ChatSessionRepositoryImpl(db)
    diary_repo = DiaryRepositoryImpl(db)
    ai = ClovaClient()
    usecase = FinalizeDiaryUseCase(chat_repo, diary_repo, ai)
    try:
        diary = await usecase.execute(session_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return DiaryResponse(
        id=diary.id,
        diary_date=diary.diary_date,
        title=diary.title,
        content=diary.content,
        emotion=diary.emotion.value,
        satisfaction=diary.satisfaction,
        chat_session_id=diary.chat_session_id,
        created_at=diary.created_at,
    )
