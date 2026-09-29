"""Isolamento dos testes, migrações e frontend sem dependência externa."""

import re
from pathlib import Path

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine

from app.config import get_settings
from app.database import Base, engine

RAIZ = Path(__file__).resolve().parent.parent


def test_suite_nunca_aponta_para_o_banco_real():
    assert get_settings().env == "test"
    assert Path(engine.url.database).name != "estoque.db"


def test_migracoes_produzem_o_mesmo_schema_dos_modelos(tmp_path):
    url = f"sqlite:///{tmp_path / 'migrado.db'}"
    cfg = Config(str(RAIZ / "alembic.ini"))
    cfg.set_main_option("script_location", str(RAIZ / "migrations"))
    cfg.set_main_option("sqlalchemy.url", url)

    command.upgrade(cfg, "head")

    eng = create_engine(url)
    with eng.connect() as conn:
        diffs = compare_metadata(MigrationContext.configure(conn), Base.metadata)
    eng.dispose()
    assert diffs == []


def test_pagina_usa_css_local_e_nao_cdn(client):
    html = client.get("/").text

    # Todo src/href precisa apontar para o próprio servidor (nenhum host externo).
    externos = [
        url for url in re.findall(r'(?:src|href)="(https?://[^"]+)"', html)
        if not url.startswith("http://testserver/")
    ]
    assert externos == []

    css = client.get("/static/css/tailwind.css")
    assert css.status_code == 200
    assert "text/css" in css.headers["content-type"]
