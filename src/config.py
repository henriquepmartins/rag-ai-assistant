"""Configuration settings for EM Vidros RAG AI Assistant."""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""

    # API Keys and Model Settings
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1/")
    MODEL_NAME = os.getenv("MODEL_NAME", "moonshotai/kimi-k2:free")

    # Vector Database Settings
    QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
    QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "emvidros_docs")
    VECTOR_DIMENSION = int(os.getenv("VECTOR_DIMENSION", "3072"))

    # SQLite Database for Session Memory
    SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "./data/sessions.db")

    # Website Scraping Settings
    WEBSITE_URL = os.getenv("WEBSITE_URL", "https://emvidros.com.br")
    MAX_PAGES = int(os.getenv("MAX_PAGES", "100"))
    SCRAPE_DELAY = float(os.getenv("SCRAPE_DELAY", "1.0"))

    # Inngest Settings
    INNGEST_APP_ID = os.getenv("INNGEST_APP_ID", "rag_app")
    INNGEST_EVENT_KEY = os.getenv("INNGEST_EVENT_KEY", "")
    INNGEST_SIGNING_KEY = os.getenv("INNGEST_SIGNING_KEY", "")

    # Application Settings
    APP_NAME = "EM Vidros AI Assistant"
    APP_DESCRIPTION = "Assistente virtual inteligente da EM Vidros"
    MAX_CHAT_HISTORY = int(os.getenv("MAX_CHAT_HISTORY", "10"))

    @classmethod
    def ensure_directories(cls):
        """Ensure required directories exist."""
        os.makedirs(os.path.dirname(cls.SQLITE_DB_PATH), exist_ok=True)
