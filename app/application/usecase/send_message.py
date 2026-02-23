from uuid import UUID

from app.application.service.ai_chat_service import AiChatService
from app.domain.model.chat_message import ChatMessage
from app.domain.model.chat_session import ChatSession
from app.domain.repository.chat_session_repository import ChatSessionRepository


class SendMessageUseCase:
    def __init__(self, repo: ChatSessionRepository, ai: AiChatService) -> None:
        self._repo = repo
        self._ai = ai

    async def execute(self, session_id: UUID, content: str) -> tuple[ChatMessage, ChatMessage, bool]:
        session = await self._repo.find_by_id(session_id)
        if not session:
            raise ValueError("세션을 찾을 수 없습니다.")
        if session.is_finalized:
            raise ValueError("이미 완료된 세션입니다.")

        user_msg = session.add_message("user", content)

        suggest = session.should_suggest_finalize
        ai_response = await self._ai.chat(session.messages, suggest_finalize=suggest)
        ai_msg = session.add_message("assistant", ai_response)

        await self._repo.save(session)
        return user_msg, ai_msg, session.should_suggest_finalize
