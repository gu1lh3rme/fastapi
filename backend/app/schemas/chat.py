"""
Schemas Pydantic v2 — Chat.
Define a estrutura de dados para o chatbot com RAG.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ChatMessageInput(BaseModel):
    """Schema de uma mensagem no histórico (para enviar ao contexto)."""
    role: str = Field(..., pattern="^(user|assistant)$", description="Papel: 'user' ou 'assistant'")
    content: str = Field(..., min_length=1, description="Conteúdo da mensagem")


class ChatRequest(BaseModel):
    """
    Schema para request do endpoint /chat.
    O frontend envia a mensagem atual + histórico da conversa.
    """
    message: str = Field(..., min_length=1, max_length=4000, description="Pergunta do usuário")
    session_id: Optional[str] = Field(None, description="ID da sessão para manter histórico")
    history: list[ChatMessageInput] = Field(
        default=[],
        max_length=20,
        description="Histórico de mensagens anteriores (máx 20)",
    )
    use_rag: bool = Field(
        default=True,
        description="Se True, busca contexto nos documentos do usuário antes de responder",
    )


class ChatSourceDocument(BaseModel):
    """Documento fonte usado pelo RAG para gerar a resposta."""
    filename: str
    content_preview: str = Field(..., description="Trecho relevante do documento")
    relevance_score: Optional[float] = None


class ChatResponse(BaseModel):
    """
    Schema de resposta do chatbot.
    Inclui a resposta gerada e os documentos fonte usados.
    """
    message_id: str
    response: str = Field(..., description="Resposta gerada pelo LLM")
    session_id: str
    sources: list[ChatSourceDocument] = Field(
        default=[],
        description="Documentos fonte usados para gerar a resposta",
    )
    model_used: str
    tokens_used: Optional[int] = None
    response_time_ms: float

    model_config = {"from_attributes": True}


class ChatHistoryResponse(BaseModel):
    """Schema de resposta para histórico de chat de uma sessão."""
    session_id: str
    messages: list[dict]
    total: int
