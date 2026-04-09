"""
Repository — Documento.
Camada de acesso ao banco de dados para operações com documentos.
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document


class DocumentRepository:
    """
    Repositório responsável por todas as operações de banco
    relacionadas ao model Document.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        user_id: str,
        filename: str,
        original_filename: str,
        content_type: str,
        file_size: int,
        file_path: str,
    ) -> Document:
        """Cria um novo registro de documento após o upload."""
        document = Document(
            user_id=user_id,
            filename=filename,
            original_filename=original_filename,
            content_type=content_type,
            file_size=file_size,
            file_path=file_path,
            status="pending",
        )
        self.db.add(document)
        await self.db.flush()
        await self.db.refresh(document)
        return document

    async def get_by_id(self, doc_id: str) -> Optional[Document]:
        """Busca documento pelo ID."""
        result = await self.db.execute(select(Document).where(Document.id == doc_id))
        return result.scalar_one_or_none()

    async def get_by_user(self, user_id: str, skip: int = 0, limit: int = 50) -> list[Document]:
        """Lista documentos de um usuário com paginação."""
        result = await self.db.execute(
            select(Document)
            .where(Document.user_id == user_id)
            .order_by(Document.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_user(self, user_id: str) -> int:
        """Conta o total de documentos de um usuário."""
        result = await self.db.execute(
            select(func.count(Document.id)).where(Document.user_id == user_id)
        )
        return result.scalar_one()

    async def update_status(
        self,
        doc_id: str,
        status: str,
        chunks_count: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> Optional[Document]:
        """Atualiza o status de processamento de um documento."""
        document = await self.get_by_id(doc_id)
        if not document:
            return None

        document.status = status
        if chunks_count is not None:
            document.chunks_count = chunks_count
        if error_message is not None:
            document.error_message = error_message
        if status == "completed":
            document.processed_at = datetime.now(timezone.utc)

        await self.db.flush()
        await self.db.refresh(document)
        return document
