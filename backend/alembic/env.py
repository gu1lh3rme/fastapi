"""
Script de ambiente do Alembic.
Configura a conexão com o banco e o contexto de execução das migrations.

Para criar nova migration:
    cd backend && alembic revision --autogenerate -m "add tabela xyz"

Para aplicar migrations:
    cd backend && alembic upgrade head

Para reverter a última migration:
    cd backend && alembic downgrade -1
"""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Importa as configurações do projeto
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.config import settings
from app.core.database import Base

# Importa todos os models para que o Alembic possa detectar as tabelas
from app.models import User, Document, ChatMessage  # noqa: F401

# Configuração de logging do Alembic
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Define os metadados dos models para autogenerate
target_metadata = Base.metadata

# Sobrescreve a URL do banco com o valor do .env
config.set_main_option("sqlalchemy.url", settings.database_url)


def run_migrations_offline() -> None:
    """
    Executa migrations no modo 'offline' (sem conexão ativa).
    Gera o SQL sem conectar ao banco — útil para revisão.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Executa as migrations na conexão fornecida."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,  # detecta mudanças de tipo de coluna
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Executa migrations de forma assíncrona (necessário para asyncpg)."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Executa migrations no modo 'online' (com conexão ativa ao banco)."""
    asyncio.run(run_async_migrations())


# Seleciona o modo de execução baseado no contexto
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
