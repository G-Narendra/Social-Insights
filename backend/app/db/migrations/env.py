"""
Alembic environment configuration for async SQLAlchemy migrations.
Supports both SQLite and PostgreSQL.
"""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection

from app.config import get_settings
from app.db.models import Base
from app.db.session import normalize_database_connection

# Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Use normalized database_url from application settings
settings = get_settings()
clean_url, _ = normalize_database_connection(settings.database_url)
config.set_main_option("sqlalchemy.url", clean_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    clean_url, _ = normalize_database_connection(settings.database_url)
    context.configure(
        url=clean_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,  # Essential for SQLite column modifications
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_as_batch=True,  # Enables batch mode for SQLite
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations asynchronously."""
    from sqlalchemy.ext.asyncio import create_async_engine

    clean_url, connect_args = normalize_database_connection(settings.database_url)

    connectable = create_async_engine(
        clean_url,
        connect_args=connect_args,
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
