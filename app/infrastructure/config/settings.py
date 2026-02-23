from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://aidiary:aidiary@localhost:5432/aidiary"
    clova_api_key: str = ""
    clova_base_url: str = "https://clovastudio.stream.ntruss.com/testapp/v1/chat-completions/HCX-005"
    clova_model: str = "HCX-005"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
