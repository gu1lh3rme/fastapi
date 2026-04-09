# Pacote de schemas Pydantic v2
from app.schemas.auth import UserRegisterRequest, UserLoginRequest, UserResponse, TokenResponse
from app.schemas.document import DocumentResponse, DocumentListResponse, DocumentUploadResponse
from app.schemas.chat import ChatRequest, ChatResponse, ChatHistoryResponse

__all__ = [
    "UserRegisterRequest", "UserLoginRequest", "UserResponse", "TokenResponse",
    "DocumentResponse", "DocumentListResponse", "DocumentUploadResponse",
    "ChatRequest", "ChatResponse", "ChatHistoryResponse",
]
