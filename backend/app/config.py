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

    # Cloudinary
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

    # Azure Speech to Text
    AZURE_SPEECH_KEY: str = ""
    AZURE_SPEECH_REGION: str = "southcentralus"
    AZURE_SPEECH_LANGUAGE: str = "es-ES"

    # Google Gemini
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"

    # Groq
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # Firebase Cloud Messaging
    FIREBASE_CREDENTIALS_PATH: str = "firebase_credentials.json"

    # Web Push (VAPID)
    VAPID_PUBLIC_KEY: str = ""
    VAPID_PRIVATE_KEY: str = ""
    VAPID_CLAIM_EMAIL: str = "admin@auxilio-vehicular.com"

    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""

    # IA local — Ollama (generación de resúmenes con Gemma 2B)
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_MODELO: str = "gemma2:2b"

    # SMTP — envío de reportes por correo (Gmail con App Password)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""

    # indicar a pydantic donde esta el .env
    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent / ".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


# Instancia unica que se reutiliza en toda la app
settings = Settings()

