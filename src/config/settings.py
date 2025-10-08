from pydantic import BaseModel
from pydantic_settings import BaseSettings
from pathlib import Path
import os

class Settings(BaseSettings):
    OPENAI_API_KEY: str | None = None
    SEMANTIC_SCHOLAR_API_KEY: str | None = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
    MODEL_TEXT: str = os.getenv("MODEL_TEXT", "gpt-4.1-mini")
    MODEL_VISION: str = os.getenv("MODEL_VISION", "gpt-4o-mini")

    MAX_BRANCHING: int = int(os.getenv("MAX_BRANCHING", 3))
    MAX_DEPTH: int = int(os.getenv("MAX_DEPTH", 4))
    EARLY_STOP_SCORE: float = float(os.getenv("EARLY_STOP_SCORE", 0.72))
    UCT_C: float = float(os.getenv("UCT_C", 1.414))

    DATA_ROOT: str = os.getenv("DATA_ROOT", "./data")
    ARTIFACT_ROOT: str = os.getenv("ARTIFACT_ROOT", "./experiments")
    SQLITE_URL: str = os.getenv("SQLITE_URL", "sqlite:///runs.db")

    HUMAN_IN_LOOP: bool = os.getenv("HUMAN_IN_LOOP", "false").lower() == "true"
    WANDB_ON: bool = os.getenv("WANDB_ON", "false").lower() == "true"

    class Config:
        env_file = ".env"
        extra = "ignore"
