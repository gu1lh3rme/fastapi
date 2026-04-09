"""
Schemas Pydantic v2 — Documentos.
Define a estrutura de dados para upload e listagem de documentos.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DocumentResponse(BaseModel):
    """Schema de resposta com dados de um documento."""
    id: str
    filename: str
    original_filename: str
    content_type: str
    file_size: int
    status: str
    error_message: Optional[str] = None
    chunks_count: Optional[int] = None
    created_at: datetime
    processed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    """Schema de resposta para listagem de documentos."""
    documents: list[DocumentResponse]
    total: int


class DocumentUploadResponse(BaseModel):
    """Schema de resposta após upload de documento."""
    message: str
    document: DocumentResponse
