"""
Serviço de autenticação.
Contém a lógica de negócio para registro e login de usuários.
"""

import logging
from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import verify_password, create_access_token
from app.repositories.user_repository import UserRepository
from app.schemas.auth import UserRegisterRequest, TokenResponse, UserResponse

logger = logging.getLogger(__name__)


async def register_user(
    request: UserRegisterRequest,
    db: AsyncSession,
) -> UserResponse:
    """
    Registra um novo usuário na plataforma.

    Valida que o email não está em uso e cria o usuário
    com a senha hasheada (nunca em texto puro!).
    """
    repo = UserRepository(db)

    # Verifica se o email já está cadastrado
    if await repo.exists_by_email(request.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este email já está cadastrado. Por favor, faça login.",
        )

    # Cria o usuário (a senha é hasheada no repository)
    user = await repo.create(
        email=request.email,
        full_name=request.full_name,
        password=request.password,
    )

    await db.commit()
    await db.refresh(user)

    logger.info(f"Novo usuário registrado: {user.email} (id: {user.id})")
    return UserResponse.model_validate(user)


async def login_user(
    email: str,
    password: str,
    db: AsyncSession,
) -> TokenResponse:
    """
    Autentica um usuário e retorna um token JWT.

    Verifica email, senha (bcrypt) e status da conta.
    Intencionalmente usa a mesma mensagem de erro para email/senha
    incorretos para não revelar quais emails estão cadastrados.
    """
    repo = UserRepository(db)
    user = await repo.get_by_email(email)

    # Verificação de credenciais — mensagem genérica por segurança
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conta desativada. Entre em contato com o suporte.",
        )

    # Gera o token JWT com o ID do usuário como subject
    access_token = create_access_token(
        data={"sub": user.id},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )

    logger.info(f"Login bem-sucedido: {user.email}")

    return TokenResponse(
        access_token=access_token,
        expires_in=settings.access_token_expire_minutes * 60,
        user=UserResponse.model_validate(user),
    )
