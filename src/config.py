"""Configurações da aplicação."""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Centraliza todas as configurações do sistema."""

    # Chaves de API e modelo
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1/")
    MODEL_NAME = os.getenv("MODEL_NAME", "moonshotai/kimi-k2:free")

    # Configurações do banco vetorial
    QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
    QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "emvidros_docs")
    VECTOR_DIMENSION = int(os.getenv("VECTOR_DIMENSION", "3072"))

    # Banco SQLite para memória de sessão
    SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "./data/sessions.db")

    # Configurações de scraping
    WEBSITE_URL = os.getenv("WEBSITE_URL", "https://emvidros.com.br")
    MAX_PAGES = int(os.getenv("MAX_PAGES", "100"))
    SCRAPE_DELAY = float(os.getenv("SCRAPE_DELAY", "1.0"))

    # Configurações Inngest
    INNGEST_APP_ID = os.getenv("INNGEST_APP_ID", "rag_app")
    INNGEST_EVENT_KEY = os.getenv("INNGEST_EVENT_KEY", "")
    INNGEST_SIGNING_KEY = os.getenv("INNGEST_SIGNING_KEY", "")

    # Configurações gerais
    APP_NAME = "EM Vidros AI Assistant"
    APP_DESCRIPTION = "Assistente virtual inteligente da EM Vidros"
    MAX_CHAT_HISTORY = int(os.getenv("MAX_CHAT_HISTORY", "10"))

    @classmethod
    def ensure_directories(cls):
        """Garante que os diretórios necessários existem."""
        os.makedirs(os.path.dirname(cls.SQLITE_DB_PATH), exist_ok=True)
