"""
Repository — Usuário.
Camada de acesso ao banco de dados para operações com usuários.
O padrão Repository separa a lógica de negócio do acesso ao banco.
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.core.security import hash_password


class UserRepository:
    """
    Repositório responsável por todas as operações de banco
    relacionadas ao model User.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Busca usuário pelo ID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """Busca usuário pelo email (usado para login)."""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def create(self, email: str, full_name: str, password: str) -> User:
        """
        Cria um novo usuário com a senha hasheada.
        Nunca armazenamos a senha em texto puro!
        """
        user = User(
            email=email,
            full_name=full_name,
            hashed_password=hash_password(password),
        )
        self.db.add(user)
        await self.db.flush()  # flush para obter o ID gerado
        await self.db.refresh(user)
        return user

    async def exists_by_email(self, email: str) -> bool:
        """Verifica se já existe um usuário com o email informado."""
        result = await self.db.execute(
            select(User.id).where(User.email == email)
        )
        return result.scalar_one_or_none() is not None
