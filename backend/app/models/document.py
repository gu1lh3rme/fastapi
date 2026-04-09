"""
Models SQLAlchemy — Documento.
Representa um arquivo (PDF, TXT, etc.) carregado pelo usuário para o RAG.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Integer, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Document(Base):
    """
    Model de documento carregado pelo usuário.
    Após o upload, o documento é processado e seus embeddings
    são armazenados no ChromaDB para uso no RAG.
    """
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    # Chave estrangeira para o usuário dono do documento
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Metadados do arquivo
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)

    # Caminho do arquivo no sistema de arquivos
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)

    # Status do processamento (pending, processing, completed, error)
    status: Mapped[str] = mapped_column(String(50), default="pending")

    # Mensagem de erro se o processamento falhar
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Número de chunks criados durante o processamento
    chunks_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relacionamento com o usuário dono
    owner: Mapped["User"] = relationship(back_populates="documents")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Document id={self.id} filename={self.original_filename} status={self.status}>"
