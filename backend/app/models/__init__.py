# Pacote de models — exporta todos para uso no Alembic
from app.models.user import User
from app.models.document import Document
from app.models.chat_message import ChatMessage

__all__ = ["User", "Document", "ChatMessage"]
