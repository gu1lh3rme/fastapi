"""
Configuração do banco de dados com SQLAlchemy 2.x (async).
Usa asyncpg como driver para PostgreSQL.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


# Cria o engine assíncrono do SQLAlchemy
# echo=True imprime as queries SQL no console (útil para debug)
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,   # verifica conexão antes de usar
    pool_size=10,
    max_overflow=20,
)

# Factory de sessões assíncronas
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    """
    Classe base para todos os modelos SQLAlchemy.
    Todos os models devem herdar desta classe.
    """
    pass


async def get_db() -> AsyncSession:
    """
    Dependency injection para obter sessão do banco.
    Uso: db: AsyncSession = Depends(get_db)
    A sessão é fechada automaticamente pelo context manager.
    O commit das transações deve ser feito explicitamente pelo serviço/router.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def create_tables():
    """
    Cria todas as tabelas no banco de dados.
    Chamado na inicialização da aplicação (apenas em dev).
    Em produção, use o Alembic para migrations.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
