from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    # LLM
    llm_provider: Literal["anthropic", "openai"] = "anthropic"
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    anthropic_model: str = "claude-haiku-4-5"
    openai_model: str = "gpt-4o-mini"

    # Storage
    r2_mock_base_path: str = "./mock_r2"

    # External services
    intranet_api_base_url: str = "http://localhost:8001"
    nerve_webhook_url: str = "http://localhost:8001/nerve/event"
    nerve_api_key: str = "dev-nerve-key"

    # Server
    iris_host: str = "0.0.0.0"
    iris_port: int = 8000
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
