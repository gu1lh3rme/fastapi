"""
Models SQLAlchemy — Mensagem de Chat.
Representa cada mensagem no histórico de conversas do chatbot.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Text, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ChatMessage(Base):
    """
    Model de mensagem de chat.
    Armazena o histórico completo de conversas entre o aluno e o chatbot.
    Inclui tanto a pergunta do usuário quanto a resposta gerada pelo LLM.
    """
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    # Chave estrangeira para o usuário
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Conteúdo da mensagem
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # "user" ou "assistant"
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Contexto utilizado pelo RAG para gerar a resposta (apenas para role=assistant)
    rag_context: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Metadados da chamada à API OpenAI
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    model_used: Mapped[str | None] = mapped_column(String(100), nullable=True)
    response_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)

    # ID da sessão de conversa (agrupa mensagens de uma mesma conversa)
    session_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Relacionamento com o usuário
    user: Mapped["User"] = relationship(back_populates="chat_messages")  # noqa: F821

    def __repr__(self) -> str:
        return f"<ChatMessage id={self.id} role={self.role} user_id={self.user_id}>"
