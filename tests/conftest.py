# Isolamento dos testes: ANTES de importar `app`, forçamos o ambiente "test" e um
# banco descartável, para que nada nesta suíte consiga tocar o estoque.db real
# (nem por acidente, se alguma rota/engine global for usada sem o override).
import os
import tempfile

os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(tempfile.mkdtemp(prefix="estoque-tests-"), "global.db")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.database import Base, enable_sqlite_foreign_keys, get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def session_factory(tmp_path):
    """Banco SQLite novo (um arquivo por teste), com o schema criado."""
    engine = create_engine(
        f"sqlite:///{tmp_path / 'test.db'}",
        connect_args={"check_same_thread": False},
    )
    enable_sqlite_foreign_keys(engine)
    Base.metadata.create_all(bind=engine)
    yield sessionmaker(bind=engine, autoflush=False)
    engine.dispose()


@pytest.fixture
def db(session_factory):
    with session_factory() as session:
        yield session


@pytest.fixture
def client(session_factory):
    def override_get_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
