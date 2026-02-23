from abc import ABC, abstractmethod

from app.domain.model.chat_message import ChatMessage


class AiChatService(ABC):
    @abstractmethod
    async def chat(self, messages: list[ChatMessage], suggest_finalize: bool = False) -> str: ...

    @abstractmethod
    async def generate_diary(self, messages: list[ChatMessage]) -> dict: ...
