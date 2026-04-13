from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class Settings(BaseSettings):

    # base de datos
    DATABASE_URL: str = "postgresql://postgres:admin@localhost:5433/db"

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 360
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # -- App ---
    APP_NAME: str = "Auxilio_vehicular_api"
    DEBUG: bool = False

    # indicar a pydantic donde esta el .env
    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent / ".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


# Instancia unica que se reutiliza en toda la app
settings = Settings()

