from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.infrastructure.config.database import engine
from app.presentation.router.chat_router import router as chat_router
from app.presentation.router.diary_router import router as diary_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()


app = FastAPI(title="AI Diary", version="0.1.0", lifespan=lifespan)


app.include_router(chat_router)
app.include_router(diary_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
