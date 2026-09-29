"""Configuração por ambiente, lida de variáveis de ambiente.

APP_ENV       dev (padrão) | test | prod
DATABASE_URL  sobrescreve o banco padrão do ambiente
"""

import os
from dataclasses import dataclass

_DEFAULT_DATABASE_URLS = {
    "dev": "sqlite:///./estoque.db",
    "test": "sqlite:///./estoque.test.db",
    "prod": "sqlite:///./estoque.db",
}


@dataclass(frozen=True)
class Settings:
    env: str
    database_url: str


def get_settings() -> Settings:
    env = os.environ.get("APP_ENV", "dev").lower()
    if env not in _DEFAULT_DATABASE_URLS:
        raise RuntimeError(f"APP_ENV inválido: {env!r} (use dev, test ou prod)")
    database_url = os.environ.get("DATABASE_URL") or _DEFAULT_DATABASE_URLS[env]
    return Settings(env=env, database_url=database_url)
