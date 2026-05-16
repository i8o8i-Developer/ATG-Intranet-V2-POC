"""
CELL Configuration — pydantic-settings based.
All values read from environment / .env file.
IST (UTC+5:30) is the ONLY timezone used throughout.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # OpenAI
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"

    # Postgres
    database_url: str = Field(..., env="DATABASE_URL")

    # Cloudflare R2
    r2_endpoint_url: str = Field(..., env="R2_ENDPOINT_URL")
    r2_access_key_id: str = Field(..., env="R2_ACCESS_KEY_ID")
    r2_secret_access_key: str = Field(..., env="R2_SECRET_ACCESS_KEY")
    r2_bucket_name: str = Field("erp-agents", env="R2_BUCKET_NAME")

    # Slack
    slack_bot_token: str = Field(..., env="SLACK_BOT_TOKEN")

    # ERP
    erp_base_url: str = Field("http://localhost:8003", env="ERP_BASE_URL")
    erp_api_key: str = Field("dev-erp-key", env="ERP_API_KEY")

    # CELL service
    cell_host: str = Field("0.0.0.0", env="CELL_HOST")
    cell_port: int = Field(8002, env="CELL_PORT")

    # Mock mode
    mock_mode: bool = Field(False, env="MOCK_MODE")
    mock_erp_url: str = Field("http://localhost:8003", env="MOCK_ERP_URL")
    mock_slack_url: str = Field("http://localhost:8004", env="MOCK_SLACK_URL")

    # Dedup
    dedup_cosine_threshold: float = 0.92
    dedup_token_overlap_threshold: float = 0.80

    # Bounty
    # Bounty is a unit count. Accountant totals units and multiplies by ₹100 to pay.
    base_hours_per_bounty: float = 4.0   # 4 hours = 1 bounty unit (normal priority)

    # Scheduler times (IST, 24h)
    schedule_morning_hour: int = 8
    schedule_morning_minute: int = 0
    schedule_eod_reminder_hour: int = 23
    schedule_eod_reminder_minute: int = 30
    schedule_night_process_hour: int = 2
    schedule_night_process_minute: int = 0

    # PM approval escalation window (hours)
    pm_approval_escalation_hours: int = 48

    # Accountability escalation thresholds
    escalate_to_apm_after: int = 3   # consecutive misses → APM
    escalate_to_dept_head_after: int = 5  # consecutive misses → Dept Head

    # ERP write retry
    erp_write_max_retries: int = 3
    erp_write_retry_base_seconds: float = 2.0

    @property
    def ist_timezone(self) -> str:
        return "Asia/Kolkata"


settings = Settings()
