"""
Router de Autenticação.
Endpoints para cadastro e login de usuários.
"""

import logging
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.auth import UserRegisterRequest, UserLoginRequest, TokenResponse, UserResponse
from app.services.auth_service import register_user, login_user
from app.utils.dependencies import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

# Cria o router com prefixo /auth
router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastro de novo usuário",
    description="Registra um novo aluno na plataforma. Email deve ser único.",
)
async def register(
    request: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Cria uma nova conta de usuário.

    - **email**: Email único do usuário
    - **full_name**: Nome completo
    - **password**: Senha (mínimo 8 caracteres, deve ter letra e número)
    """
    return await register_user(request, db)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login do usuário",
    description="Autentica o usuário e retorna um token JWT Bearer.",
)
async def login(
    request: UserLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Realiza login e retorna token de acesso JWT.

    Use o token retornado no header `Authorization: Bearer <token>`
    para acessar os endpoints protegidos.
    """
    return await login_user(request.email, request.password, db)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Dados do usuário logado",
    description="Retorna os dados do usuário autenticado.",
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """
    Retorna os dados do usuário atualmente autenticado.
    Requer token JWT válido no header Authorization.
    """
    return UserResponse.model_validate(current_user)
