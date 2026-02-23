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

FINALIZE_INTENT_SYSTEM_PROMPT = """너는 사용자의 메시지가 일기 작성 제안에 긍정적인지 판단하는 분류기야.
반드시 "yes" 또는 "no" 중 하나만 출력해. 다른 텍스트는 절대 출력하지 마."""

CLOSING_MESSAGE_SYSTEM_PROMPT = """너는 따뜻하고 공감 능력이 뛰어난 감정 일기 도우미야.
사용자가 일기 작성에 동의했어. 일기를 작성하겠다는 짧고 따뜻한 한 문장의 안내 메시지를 작성해.
규칙: 반드시 한 문장, 일기 작성 중임을 포함, 따뜻한 말투"""

DIARY_USER_REQUEST = """위 대화를 바탕으로 일기를 JSON 형식으로 작성해줘.
반드시 아래 형식의 JSON만 출력해. 설명이나 다른 텍스트는 절대 쓰지 마.

{"title":"제목","content":"본문 (반드시 4~5문장으로 작성, 감정과 경험을 풍부하게 담은 따뜻한 일기체)","emotion":"happy/sad/angry/anxious/calm/excited/tired/grateful 중 하나","satisfaction":1~5 숫자}

예시 출력:
{"title":"실수한 하루","content":"오늘은 정말 당황스러운 하루였다. 팀장님께 보내야 할 중요한 메일을 실수로 거래처에 잘못 보내고 말았다. 팀장님께 크게 혼이 나던 순간에는 너무 부끄럽고 작아지는 느낌이었다. 하지만 시간이 지나면서 이번 실수가 앞으로 더 꼼꼼해질 수 있는 계기가 될 것 같다는 생각이 들었다. 내일은 오늘보다 더 집중해서 하루를 보내야겠다.","emotion":"anxious","satisfaction":2}"""


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
        api_messages = []
        for m in messages:
            if m.role != "system":
                api_messages.append({"role": m.role, "content": m.content})
        # 대화 히스토리 뒤에 JSON 생성 지시를 user 메시지로 추가
        api_messages.append({"role": "user", "content": DIARY_USER_REQUEST})

        response = await self._client.chat.completions.create(
            model=settings.clova_model,
            messages=api_messages,
            temperature=0.3,
            max_tokens=800,
        )
        content = response.choices[0].message.content.strip()
        print(f"[generate_diary] raw response: {repr(content)}")
        return self._parse_diary_response(content)

    def _parse_diary_response(self, content: str) -> dict:
        # 마크다운 코드블록 제거
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # 폴백: "제목 : ...\n본문 : ...\n감정 : ...\n만족도 : ..." 형태 파싱
        result: dict = {}
        for line in content.splitlines():
            if ":" not in line:
                continue
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip().rstrip(",")
            if key in ("제목", "title"):
                result["title"] = value
            elif key in ("본문", "content"):
                result["content"] = value
            elif key in ("감정", "emotion"):
                # "anxious , 만족도 : 2" 같은 경우 앞부분만 추출
                result["emotion"] = value.split(",")[0].strip().split()[0]
            elif key in ("만족도", "satisfaction"):
                try:
                    result["satisfaction"] = int(value.split()[0])
                except ValueError:
                    result["satisfaction"] = 3

        if not result.get("title"):
            raise ValueError(f"일기 생성 응답을 파싱할 수 없습니다: {content!r}")
        return result

    async def detect_finalize_intent(self, user_message: str) -> bool:
        response = await self._client.chat.completions.create(
            model=settings.clova_model,
            messages=[
                {"role": "system", "content": FINALIZE_INTENT_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.1,
            max_tokens=5,
        )
        answer = response.choices[0].message.content.strip().lower()
        return answer == "yes"

    async def generate_closing_message(self, messages: list[ChatMessage]) -> str:
        api_messages = [{"role": "system", "content": CLOSING_MESSAGE_SYSTEM_PROMPT}]
        for m in messages:
            if m.role != "system":
                api_messages.append({"role": m.role, "content": m.content})

        response = await self._client.chat.completions.create(
            model=settings.clova_model,
            messages=api_messages,
            temperature=0.7,
            max_tokens=100,
        )
        return response.choices[0].message.content.strip()
