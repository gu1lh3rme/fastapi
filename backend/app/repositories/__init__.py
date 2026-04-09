# Pacote de repositories — acesso ao banco de dados
from app.repositories.user_repository import UserRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.chat_repository import ChatRepository

__all__ = ["UserRepository", "DocumentRepository", "ChatRepository"]
