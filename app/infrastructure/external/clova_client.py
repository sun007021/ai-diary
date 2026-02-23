import json

from openai import AsyncOpenAI

from app.application.service.ai_chat_service import AiChatService
from app.domain.model.chat_message import ChatMessage
from app.infrastructure.config.settings import settings

CHAT_SYSTEM_PROMPT = """너는 따뜻하고 공감 능력이 뛰어난 감정 일기 도우미야.
사용자의 하루에 대해 자연스럽게 대화하며, 감정과 경험을 이끌어내.

규칙:
- 한 번에 하나의 질문만 해
- 공감하고 경청하는 태도로 대화해
- 사용자의 감정을 있는 그대로 수용해
- 짧고 따뜻한 문장으로 답해"""

CHAT_FINALIZE_HINT = "\n- 대화가 충분히 진행되었으니, 답변 마지막에 자연스럽게 '오늘 이야기를 일기로 정리해 볼까요?' 같은 제안을 해"

DIARY_SYSTEM_PROMPT = """너는 대화 내용을 바탕으로 일기를 작성하는 AI야.
반드시 아래 JSON 형식으로만 응답해. 다른 텍스트 없이 JSON만 출력해.

{
  "title": "일기 제목 (짧고 감성적으로)",
  "content": "일기 본문 (3-5문장, 하루를 요약하는 따뜻한 일기체)",
  "emotion": "감정 (happy, sad, angry, anxious, calm, excited, tired, grateful 중 하나)",
  "satisfaction": 만족도 (1-5 정수)
}"""


class ClovaClient(AiChatService):
    def __init__(self) -> None:
        self._client = AsyncOpenAI(
            api_key=settings.clova_api_key,
            base_url=settings.clova_base_url,
        )

    async def chat(self, messages: list[ChatMessage], suggest_finalize: bool = False) -> str:
        system_prompt = CHAT_SYSTEM_PROMPT
        if suggest_finalize:
            system_prompt += CHAT_FINALIZE_HINT

        api_messages = [{"role": "system", "content": system_prompt}]
        for m in messages:
            if m.role != "system":
                api_messages.append({"role": m.role, "content": m.content})

        response = await self._client.chat.completions.create(
            model=settings.clova_model,
            messages=api_messages,
            temperature=0.7,
            max_tokens=500,
        )
        return response.choices[0].message.content

    async def generate_diary(self, messages: list[ChatMessage]) -> dict:
        api_messages = [{"role": "system", "content": DIARY_SYSTEM_PROMPT}]
        for m in messages:
            if m.role != "system":
                api_messages.append({"role": m.role, "content": m.content})

        response = await self._client.chat.completions.create(
            model=settings.clova_model,
            messages=api_messages,
            temperature=0.3,
            max_tokens=800,
        )
        content = response.choices[0].message.content.strip()
        return json.loads(content)
