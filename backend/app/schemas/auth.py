"""
Schemas Pydantic v2 — Autenticação e Usuário.
Define a estrutura de dados para requests e responses da API.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


# ─── Request Schemas ────────────────────────────────────────────────


class UserRegisterRequest(BaseModel):
    """Schema para cadastro de novo usuário."""
    email: EmailStr = Field(..., description="Email do usuário")
    full_name: str = Field(..., min_length=2, max_length=255, description="Nome completo")
    password: str = Field(..., min_length=8, max_length=100, description="Senha")

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        """Valida que a senha tem pelo menos uma letra e um número."""
        if not any(c.isalpha() for c in v):
            raise ValueError("A senha deve conter pelo menos uma letra")
        if not any(c.isdigit() for c in v):
            raise ValueError("A senha deve conter pelo menos um número")
        return v


class UserLoginRequest(BaseModel):
    """Schema para login de usuário."""
    email: EmailStr = Field(..., description="Email do usuário")
    password: str = Field(..., description="Senha")


# ─── Response Schemas ───────────────────────────────────────────────


class UserResponse(BaseModel):
    """Schema de resposta com dados do usuário (sem senha)."""
    id: str
    email: str
    full_name: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """Schema de resposta com token JWT após login bem-sucedido."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Tempo de expiração em segundos")
    user: UserResponse
