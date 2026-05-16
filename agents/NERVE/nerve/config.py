from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Dict, Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str

    # Agent URLs
    iris_base_url: str = "http://localhost:8000"
    cell_base_url: str = "http://localhost:8002"
    cortex_base_url: str = "http://localhost:8004"
    stroma_base_url: str = "http://localhost:8005"
    
    # Auth
    nerve_api_key: str
    
    # Slack
    slack_bot_token: Optional[str] = None
    slack_admin_channel: Optional[str] = None
    
    # Service
    nerve_host: str = "0.0.0.0"
    nerve_port: int = 8001
    mock_mode: bool = False
    timezone: str = "Asia/Kolkata"

    # Timeouts (seconds)
    default_job_timeout: int = 60
    aggregation_job_timeout: int = 300

    @property
    def agent_urls(self) -> dict:
        return {
            "iris": self.iris_base_url, 
            "cell": self.cell_base_url,
            "cortex": self.cortex_base_url, 
            "stroma": self.stroma_base_url,
        }

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
