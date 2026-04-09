"""
Configurações centrais da aplicação.
Todas as variáveis de ambiente são lidas aqui via pydantic-settings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """
    Classe principal de configurações.
    Os valores são carregados automaticamente do arquivo .env.
    """

    # --- Aplicação ---
    app_name: str = "RAG Chatbot - Área do Aluno"
    app_version: str = "1.0.0"
    debug: bool = False

    # --- Banco de Dados ---
    database_url: str = "postgresql+asyncpg://postgres:admin@localhost:5432/rag_chatbot"

    # --- OpenAI ---
    openai_api_key: str = ""
    openai_chat_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"

    # --- JWT ---
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # --- Upload de Arquivos ---
    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 20

    # --- ChromaDB ---
    chroma_persist_dir: str = "./chroma_db"

    # Configura o pydantic-settings para ler o arquivo .env
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Retorna uma instância singleton das configurações.
    O decorator @lru_cache garante que o .env é lido apenas uma vez.
    """
    return Settings()


# Instância global para uso direto
settings = get_settings()
