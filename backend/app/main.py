"""
Ponto de entrada principal da aplicação FastAPI.

Para rodar:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Documentação automática disponível em:
    http://localhost:8000/docs  (Swagger UI)
    http://localhost:8000/redoc (ReDoc)
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.routers import auth_router, documents_router, chat_router

# Configuração de logging — exibe logs formatados no console
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia o ciclo de vida da aplicação.
    Código ANTES do yield: executado ao iniciar.
    Código APÓS o yield: executado ao encerrar.
    """
    logger.info(f"🚀 Iniciando {settings.app_name} v{settings.app_version}")
    logger.info(f"📊 Banco de dados: {settings.database_url.split('@')[-1]}")
    logger.info(f"🤖 Modelo OpenAI: {settings.openai_chat_model}")

    # Garante que os diretórios necessários existam
    import os
    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs(settings.chroma_persist_dir, exist_ok=True)
    logger.info(f"📁 Diretório de uploads: {settings.upload_dir}")
    logger.info(f"🗄️  ChromaDB: {settings.chroma_persist_dir}")

    yield  # Aplicação rodando

    logger.info("🛑 Encerrando aplicação...")


# ─── Criação da Aplicação FastAPI ──────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
## RAG Chatbot — Área do Aluno 🎓

Backend FastAPI para um chatbot educacional com RAG (Retrieval Augmented Generation).

### Funcionalidades
- 🔐 **Autenticação** com JWT
- 📄 **Upload de documentos** (PDF, TXT, DOCX) para o RAG
- 🤖 **Chat inteligente** com contexto dos seus documentos
- 🔍 **RAG completo** com ChromaDB + OpenAI Embeddings

### Como usar
1. Cadastre-se em `/auth/register`
2. Faça login em `/auth/login` para obter o token
3. Use o token no header `Authorization: Bearer <token>`
4. Faça upload de documentos em `/documents/upload`
5. Converse com o chatbot em `/chat`
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ─── CORS — Permite requisições do frontend Angular ────────────────
# Em produção, substitua os origins pelos domínios específicos do seu frontend
# Exemplo: allow_origins=["https://meu-app.com", "http://localhost:4200"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://localhost:3000"],  # Angular dev server
    allow_credentials=False,   # não use True com allow_origins=["*"]
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

# ─── Registro dos Routers ──────────────────────────────────────────
app.include_router(auth_router,      prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")
app.include_router(chat_router,      prefix="/api/v1")


# ─── Endpoints Básicos ─────────────────────────────────────────────

@app.get("/", tags=["Root"], summary="Health check básico")
async def root():
    """Verifica se a API está no ar."""
    return {
        "status": "online",
        "app": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
    }


@app.get("/health", tags=["Root"], summary="Health check detalhado")
async def health_check():
    """Verifica o status da aplicação e suas dependências."""
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "app": settings.app_name,
            "version": settings.app_version,
            "model": settings.openai_chat_model,
        },
    )
