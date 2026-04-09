"""
Serviço de upload e gerenciamento de documentos.
Coordena o upload, processamento e listagem de documentos do usuário.
"""

import logging
from pathlib import Path

from fastapi import HTTPException, UploadFile, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import User
from app.repositories.document_repository import DocumentRepository
from app.schemas.document import DocumentResponse, DocumentListResponse, DocumentUploadResponse
from app.utils.helpers import generate_unique_filename, ensure_upload_dir, is_allowed_file
from app.services.rag_service import process_document

logger = logging.getLogger(__name__)

# Tamanho máximo de upload em bytes
MAX_FILE_SIZE_BYTES = settings.max_upload_size_mb * 1024 * 1024


async def upload_document(
    file: UploadFile,
    current_user: User,
    db: AsyncSession,
    background_tasks: BackgroundTasks,
) -> DocumentUploadResponse:
    """
    Faz o upload de um documento e inicia o processamento em background.

    Etapas:
    1. Valida o tipo e tamanho do arquivo
    2. Salva o arquivo no sistema de arquivos
    3. Cria o registro no banco (status='pending')
    4. Inicia processamento RAG em background
    5. Retorna imediatamente ao usuário (não espera o processamento)

    O processamento em background evita timeout para arquivos grandes.
    """
    # Validação: tipo de arquivo
    if not is_allowed_file(file.filename or "", file.content_type or ""):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de arquivo não suportado: {file.content_type}. "
                   f"Use PDF, TXT, MD ou DOCX.",
        )

    # Lê o arquivo e valida o tamanho
    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Arquivo muito grande. Máximo: {settings.max_upload_size_mb}MB",
        )

    # Salva o arquivo no disco com nome único
    upload_dir = ensure_upload_dir(settings.upload_dir)
    unique_filename = generate_unique_filename(file.filename or "documento")
    # Organiza por usuário
    user_dir = upload_dir / current_user.id
    user_dir.mkdir(exist_ok=True)
    file_path = user_dir / unique_filename

    file_path.write_bytes(file_content)
    logger.info(f"Arquivo salvo: {file_path}")

    # Cria registro no banco de dados
    repo = DocumentRepository(db)
    document = await repo.create(
        user_id=current_user.id,
        filename=unique_filename,
        original_filename=file.filename or unique_filename,
        content_type=file.content_type or "application/octet-stream",
        file_size=len(file_content),
        file_path=str(file_path),
    )

    # Persiste o registro antes de lançar a task em background
    await db.commit()
    await db.refresh(document)

    # Inicia processamento RAG em background
    # O usuário recebe a resposta imediatamente enquanto o processamento ocorre
    background_tasks.add_task(
        _process_document_background,
        doc_id=document.id,
        file_path=str(file_path),
        content_type=file.content_type or "",
        user_id=current_user.id,
    )

    return DocumentUploadResponse(
        message="Documento recebido! O processamento foi iniciado em background.",
        document=DocumentResponse.model_validate(document),
    )


async def _process_document_background(
    doc_id: str,
    file_path: str,
    content_type: str,
    user_id: str,
) -> None:
    """
    Tarefa em background: processa o documento e atualiza o status no banco.
    Chamada pelo BackgroundTasks do FastAPI após o upload.
    """
    # Importa aqui para evitar circular import com dependências async
    from app.core.database import AsyncSessionLocal
    from app.repositories.document_repository import DocumentRepository

    logger.info(f"Iniciando processamento em background: documento {doc_id}")

    async with AsyncSessionLocal() as db:
        repo = DocumentRepository(db)
        try:
            # Marca como 'processing'
            await repo.update_status(doc_id, "processing")
            await db.commit()

            # Processa o documento (chunks + embeddings + ChromaDB)
            chunks_count = await process_document(
                file_path=file_path,
                content_type=content_type,
                user_id=user_id,
                document_id=doc_id,
            )

            # Marca como concluído
            await repo.update_status(doc_id, "completed", chunks_count=chunks_count)
            await db.commit()
            logger.info(f"Documento {doc_id} processado: {chunks_count} chunks")

        except Exception as e:
            logger.error(f"Erro ao processar documento {doc_id}: {e}")
            await repo.update_status(doc_id, "error", error_message=str(e))
            await db.commit()


async def list_documents(
    current_user: User,
    db: AsyncSession,
    skip: int = 0,
    limit: int = 50,
) -> DocumentListResponse:
    """Lista todos os documentos do usuário com paginação."""
    repo = DocumentRepository(db)
    documents = await repo.get_by_user(current_user.id, skip=skip, limit=limit)
    total = await repo.count_by_user(current_user.id)

    return DocumentListResponse(
        documents=[DocumentResponse.model_validate(d) for d in documents],
        total=total,
    )
