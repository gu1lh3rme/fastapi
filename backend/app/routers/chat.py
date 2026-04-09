"""
Router de Chat.
Endpoint principal do chatbot com RAG integrado.
"""

import logging
import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse, ChatHistoryResponse
from app.services.openai_service import generate_chat_response
from app.repositories.chat_repository import ChatRepository
from app.utils.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post(
    "",
    response_model=ChatResponse,
    summary="Enviar mensagem ao chatbot",
    description="""
    Envia uma mensagem ao assistente IA com suporte a RAG.
    
    **Fluxo RAG completo:**
    1. Recebe a pergunta do usuário
    2. Busca os trechos mais relevantes nos documentos do usuário (ChromaDB)
    3. Injeta o contexto no prompt
    4. Chama o GPT-4o-mini com o contexto + histórico da conversa
    5. Retorna a resposta com as fontes utilizadas
    
    **Dica:** Envie documentos primeiro via `/documents/upload` para melhorar as respostas.
    """,
)
async def send_message(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    """
    Envia mensagem e recebe resposta do chatbot com RAG.

    - **message**: Pergunta ou mensagem do usuário
    - **session_id**: ID da sessão (cria nova se não informado)
    - **history**: Histórico de mensagens anteriores para contexto
    - **use_rag**: Se deve buscar contexto nos documentos (padrão: true)
    """
    # Gera session_id se não fornecido
    session_id = request.session_id or str(uuid.uuid4())

    # Converte histórico para formato esperado pelo service
    history = [{"role": h.role, "content": h.content} for h in request.history]

    # Chama o serviço de geração de resposta (RAG + LLM)
    result = await generate_chat_response(
        user_id=current_user.id,
        message=request.message,
        history=history,
        use_rag=request.use_rag,
    )

    # Salva as mensagens no banco de dados (histórico persistente)
    chat_repo = ChatRepository(db)

    # Salva mensagem do usuário
    await chat_repo.save_message(
        user_id=current_user.id,
        role="user",
        content=request.message,
        session_id=session_id,
    )

    # Salva resposta do assistente
    saved_msg = await chat_repo.save_message(
        user_id=current_user.id,
        role="assistant",
        content=result["response"],
        session_id=session_id,
        rag_context=result.get("rag_context"),
        tokens_used=result.get("tokens_used"),
        model_used=result.get("model_used"),
        response_time_ms=result.get("response_time_ms"),
    )

    # Persiste as mensagens no banco
    await db.commit()

    return ChatResponse(
        message_id=saved_msg.id,
        response=result["response"],
        session_id=session_id,
        sources=result.get("sources", []),
        model_used=result["model_used"],
        tokens_used=result.get("tokens_used"),
        response_time_ms=result["response_time_ms"],
    )


@router.get(
    "/history/{session_id}",
    response_model=ChatHistoryResponse,
    summary="Histórico de uma sessão de chat",
    description="Retorna todas as mensagens de uma sessão específica.",
)
async def get_chat_history(
    session_id: str,
    limit: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatHistoryResponse:
    """Retorna o histórico de mensagens de uma sessão de chat."""
    chat_repo = ChatRepository(db)
    messages = await chat_repo.get_session_history(
        user_id=current_user.id,
        session_id=session_id,
        limit=limit,
    )

    return ChatHistoryResponse(
        session_id=session_id,
        messages=[
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "created_at": m.created_at.isoformat(),
            }
            for m in messages
        ],
        total=len(messages),
    )


@router.get(
    "/sessions",
    summary="Listar sessões de chat do usuário",
    description="Retorna os IDs de todas as sessões de chat do usuário.",
)
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Lista todas as sessões de chat do usuário autenticado."""
    chat_repo = ChatRepository(db)
    sessions = await chat_repo.get_user_sessions(current_user.id)
    return {"sessions": sessions, "total": len(sessions)}
