from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    OPENAI_API_KEY: SecretStr | None = None
    SEMANTIC_SCHOLAR_API_KEY: str | None = None
    MODEL_TEXT: str = "gpt-4.1-mini"
    MODEL_VISION: str = "gpt-4o-mini"

    MAX_BRANCHING: int = 3
    MAX_DEPTH: int = 4
    EARLY_STOP_SCORE: float = 0.72
    UCT_C: float = 1.414

    DATA_ROOT: str = "./data"
    ARTIFACT_ROOT: str = "./experiments"
    SQLITE_URL: str = "sqlite:///runs.db"

    HUMAN_IN_LOOP: bool = False
    WANDB_ON: bool = False
    WANDB_PROJECT: str = "ChicoCienciaV1"

    # Semantic Scholar rate limiting
    SEMANTIC_SCHOLAR_RATE_LIMIT: float = 1.1
    SEMANTIC_SCHOLAR_CACHE_TTL: int = 3600

    def require_openai_api_key(self) -> str:
        if self.OPENAI_API_KEY is None:
            raise ValueError("OPENAI_API_KEY não configurada.")
        value = self.OPENAI_API_KEY.get_secret_value().strip()
        if not value:
            raise ValueError("OPENAI_API_KEY não configurada.")
        return value
