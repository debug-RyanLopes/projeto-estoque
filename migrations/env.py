"""Ambiente do Alembic: usa a mesma URL de banco e os mesmos modelos da aplicação."""

from alembic import context
from sqlalchemy import create_engine

from app import models  # noqa: F401  (registra as tabelas em Base.metadata)
from app.config import get_settings
from app.database import Base

config = context.config
target_metadata = Base.metadata


def _database_url() -> str:
    # `-x url=...` (linha de comando) > sqlalchemy.url (ini/testes) > app.config
    return (
        context.get_x_argument(as_dictionary=True).get("url")
        or config.get_main_option("sqlalchemy.url")
        or get_settings().database_url
    )


def run_migrations_offline() -> None:
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        render_as_batch=True,  # SQLite não faz ALTER TABLE completo; o batch recria a tabela
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(_database_url())
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
