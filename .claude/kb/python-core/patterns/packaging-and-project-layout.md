# Empacotamento e Layout de Projeto

## `pyproject.toml` como fonte única de configuração

```toml
[project]
name = "projeto-estoque"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "anthropic>=0.40",
]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "UP"]  # erros, pyflakes, import sort, pyupgrade

[tool.pytest.ini_options]
testpaths = ["tests"]
```

Prefira `pyproject.toml` a `setup.py`/`setup.cfg`/`requirements.txt` separados
para projetos novos — uma fonte de verdade para dependências, versão mínima de
Python e config de ferramentas (ruff, pytest, mypy).

## Layout `src/` vs layout plano

```text
# Layout src/ (recomendado para pacotes distribuíveis/instaláveis)
projeto/
├── pyproject.toml
├── src/
│   └── projeto_estoque/
│       ├── __init__.py
│       └── produtos.py
└── tests/
    └── test_produtos.py

# Layout plano (aceitável para scripts/apps simples, não-distribuídos)
projeto/
├── pyproject.toml
├── main.py
└── tests/
    └── test_main.py
```

Layout `src/` evita importar acidentalmente o pacote local não-instalado em vez
da versão instalada (`pip install -e .`) — importante quando o projeto vai virar
uma biblioteca. Para um app simples de arquivo único (como scripts CLI), layout
plano é suficiente e não vale a complexidade extra.

## Ambientes virtuais

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Nunca instalar dependências de projeto no Python global. `.venv/` sempre no
`.gitignore`.

## Linters e formatters recomendados

| Ferramenta | Papel |
|---|---|
| `ruff` | Lint + formatação rápida (substitui flake8+isort+black em um binário) |
| `mypy` ou `pyright` | Checagem de tipos estática |
| `pytest` + `pytest-cov` | Testes + cobertura |

Ao revisar código, sempre checar se `pyproject.toml`/`.flake8`/`ruff.toml`
já configura essas ferramentas — rodar via Bash (`ruff check .`, `mypy .`) antes
de propor mudanças manualmente equivalentes ao que o linter já detectaria.

## Dependências: fixar versão ou não?

- Aplicação final (não é biblioteca de terceiros) → fixar versões exatas ou com
  range estreito em `requirements.txt`/lockfile, para builds reprodutíveis.
- Biblioteca publicada para outros usarem → declarar range compatível amplo em
  `pyproject.toml` (`anthropic>=0.40,<1.0`), para não conflitar com o que o
  consumidor já usa.
