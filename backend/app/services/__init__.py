# Pacote de services — lógica de negócio
from app.services.auth_service import register_user, login_user
from app.services.document_service import upload_document, list_documents
from app.services.openai_service import generate_chat_response

__all__ = [
    "register_user", "login_user",
    "upload_document", "list_documents",
    "generate_chat_response",
]
