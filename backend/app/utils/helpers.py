"""
Utilitários — Funções auxiliares gerais.
"""

import os
import uuid
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Tipos de arquivo permitidos para upload
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "text/plain",
    "text/markdown",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
}

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md", ".docx", ".doc"}


def generate_unique_filename(original_filename: str) -> str:
    """
    Gera um nome de arquivo único para evitar conflitos no sistema de arquivos.
    Ex: "meu-doc.pdf" -> "a1b2c3d4-meu-doc.pdf"
    """
    ext = Path(original_filename).suffix.lower()
    unique_id = str(uuid.uuid4())[:8]
    safe_name = Path(original_filename).stem.replace(" ", "_")[:50]
    return f"{unique_id}_{safe_name}{ext}"


def ensure_upload_dir(upload_dir: str) -> Path:
    """Garante que o diretório de upload existe."""
    path = Path(upload_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def is_allowed_file(filename: str, content_type: str) -> bool:
    """
    Verifica se o arquivo enviado tem extensão e tipo MIME permitidos.
    Importante para segurança: impede upload de arquivos maliciosos.
    """
    ext = Path(filename).suffix.lower()
    return ext in ALLOWED_EXTENSIONS and content_type in ALLOWED_MIME_TYPES


def format_file_size(size_bytes: int) -> str:
    """Formata o tamanho de arquivo para exibição amigável."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
