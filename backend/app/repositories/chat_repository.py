"""
Repository — Mensagem de Chat.
Camada de acesso ao banco de dados para histórico de conversas.
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat_message import ChatMessage


class ChatRepository:
    """
    Repositório responsável por todas as operações de banco
    relacionadas ao model ChatMessage.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def save_message(
        self,
        user_id: str,
        role: str,
        content: str,
        session_id: Optional[str] = None,
        rag_context: Optional[str] = None,
        tokens_used: Optional[int] = None,
        model_used: Optional[str] = None,
        response_time_ms: Optional[float] = None,
    ) -> ChatMessage:
        """Salva uma mensagem no histórico de chat."""
        message = ChatMessage(
            user_id=user_id,
            role=role,
            content=content,
            session_id=session_id,
            rag_context=rag_context,
    tokens_used=tokens_used,
            model_used=model_used,
            response_time_ms=response_time_ms,
        )
        self.db.add(message)
        await self.db.flush()
        await self.db.refresh(message)
        return message

    async def get_session_history(
        self,
        user_id: str,
        session_id: str,
        limit: int = 20,
    ) -> list[ChatMessage]:
        """Retorna o histórico de uma sessão de chat ordenado por data."""
        result = await self.db.execute(
            select(ChatMessage)
            .where(
                ChatMessage.user_id == user_id,
                ChatMessage.session_id == session_id,
            )
            .order_by(ChatMessage.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_user_sessions(self, user_id: str) -> list[str]:
        """Retorna os IDs das sessões de chat de um usuário."""
        result = await self.db.execute(
            select(ChatMessage.session_id)
            .where(
                ChatMessage.user_id == user_id,
                ChatMessage.session_id.isnot(None),
            )
            .distinct()
        )
        return [row[0] for row in result.fetchall()]
