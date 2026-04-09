# Pacote de routers — exporta todos para registro no main.py
from app.routers.auth import router as auth_router
from app.routers.documents import router as documents_router
from app.routers.chat import router as chat_router

__all__ = ["auth_router", "documents_router", "chat_router"]
