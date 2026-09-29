"""Conexão com o banco (SQLite por padrão; a URL vem de app.config)."""

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import get_settings

settings = get_settings()

# check_same_thread=False: as rotas síncronas rodam em threads do pool do FastAPI,
# e o SQLite por padrão proíbe usar a conexão em outra thread.
engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def enable_sqlite_foreign_keys(engine: Engine) -> None:
    """SQLite ignora FOREIGN KEY por padrão; liga a checagem em cada conexão."""

    @event.listens_for(engine, "connect")
    def _fk_on(dbapi_connection, _record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


enable_sqlite_foreign_keys(engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
