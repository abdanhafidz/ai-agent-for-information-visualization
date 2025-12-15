import os
from typing import List, ClassVar

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Configs(BaseSettings):
    # ========= BASE =========
    ENV: str = os.getenv("ENV", "dev")

    API: str = "/api"
    API_V1_STR: str = "/api/v1"
    API_V2_STR: str = "/api/v2"
    PROJECT_NAME: str = "fca-api"

    ENV_DATABASE_MAPPER: ClassVar[dict] = {
        "prod": "fca",
        "stage": "stage-fca",
        "dev": "dev-fca",
        "test": "test-fca",
    }

    DB_ENGINE_MAPPER: ClassVar[dict] = {
        "postgresql": "postgresql+psycopg",
        "postgres": "postgresql+psycopg",
        "mysql": "mysql+pymysql",
    }

    PROJECT_ROOT: str = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )

    # ========= AUTH =========
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30

    # ========= CORS =========
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    # ========= DATABASE =========
    DB: str = os.getenv("DB", "postgresql")
    DB_USER: str = os.getenv("DB_USER", "")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_HOST: str = os.getenv("DB_HOST", "")
    DB_PORT: str = os.getenv("DB_PORT", "5432")

    @property
    def DB_ENGINE(self) -> str:
        return self.DB_ENGINE_MAPPER[self.DB]

    @property
    def DATABASE_NAME(self) -> str:
        return "postgres"

    @property
    def DATABASE_URI(self) -> str:
        return (
            f"{self.DB_ENGINE}://"
            f"{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}"
            f"/{self.DATABASE_NAME}"
            f"?sslmode=require"
        )

    # ========= PAGINATION =========
    PAGE: int = 1
    PAGE_SIZE: int = 20
    ORDERING: str = "-id"

    class Config:
        case_sensitive = True


configs = Configs()
