"""
Router de Documentos.
Endpoints para upload e listagem de documentos para o RAG.
"""

import logging
from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.schemas.document import DocumentListResponse, DocumentUploadResponse, DocumentResponse
from app.services.document_service import upload_document, list_documents
from app.utils.dependencies import get_current_user

logger = logging.getLogger(__name__)

# Router para documentos — requer autenticação em todos os endpoints
router = APIRouter(
    prefix="/documents",
    tags=["Documentos"],
    dependencies=[Depends(get_current_user)],
)


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload de documento para o RAG",
    description="""
    Faz o upload de um documento (PDF, TXT, DOCX) para ser processado pelo RAG.
    
    O processamento ocorre em background:
    1. O arquivo é salvo no servidor
    2. Retorna imediatamente com status 'pending'
    3. Em background: extrai texto → divide em chunks → gera embeddings → armazena no ChromaDB
    
    Use GET /documents para verificar quando o status mudar para 'completed'.
    """,
)
async def upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Arquivo para upload (PDF, TXT, MD ou DOCX)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentUploadResponse:
    """
    Upload de documento para processamento RAG.
    Tipos aceitos: PDF, TXT, MD, DOCX (máximo 20MB).
    """
    return await upload_document(file, current_user, db, background_tasks)


@router.get(
    "",
    response_model=DocumentListResponse,
    summary="Listar documentos do usuário",
    description="Retorna todos os documentos enviados pelo usuário com seus status de processamento.",
)
async def list_user_documents(
    skip: int = Query(default=0, ge=0, description="Número de itens para pular (paginação)"),
    limit: int = Query(default=50, ge=1, le=100, description="Máximo de itens por página"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentListResponse:
    """
    Lista todos os documentos do usuário autenticado.
    
    Status possíveis:
    - **pending**: Aguardando processamento
    - **processing**: Em processamento
    - **completed**: Pronto para uso no RAG
    - **error**: Erro no processamento (ver campo error_message)
    """
    return await list_documents(current_user, db, skip=skip, limit=limit)
