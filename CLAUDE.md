# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A local, single-user stock-control (estoque) web app: FastAPI + SQLAlchemy 2.0 + SQLite + Jinja2
templates (server-rendered, Tailwind CSS built locally). Features: product registration,
entrada/saida movements, low-stock alert. No external services, API keys or paid dependencies are used.

## Setup and running

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head            # creates/updates estoque.db
uvicorn app.main:app --reload   # or: make run
pytest                          # or: make test
```

## Architecture

- [app/main.py](app/main.py) — routes only. Routes are plain `def` (not `async def`) on purpose:
  SQLAlchemy is synchronous, so FastAPI must run them in its threadpool. They translate HTTP ->
  service call -> redirect, mapping `services.EstoqueError` subclasses to `/?erro=...`.
- [app/services.py](app/services.py) — all business rules. Two concurrency decisions live here:
  stock changes are a single conditional `UPDATE ... SET quantidade = quantidade + delta
  [WHERE quantidade >= q]` (no read-modify-write), and product creation relies on the UNIQUE
  constraint on `sku` (catch `IntegrityError`) instead of check-then-insert. The initial stock given
  at registration is also recorded as an "entrada" movement (same transaction), so the history always
  sums to the balance (`quantidade == entradas - saidas`); keep that invariant. Deleting a product
  logs a `tipo="exclusao"` movement (quantidade = balance at deletion) that is informational only and
  must not be counted in that sum.
  `listar_movimentacoes` feeds the collapsible "Registro de movimentações" section of the dashboard.
- [app/models.py](app/models.py) — `Produto` (soft-deleted via `ativo`) and `Movimentacao`, an
  append-only history: ORM `before_update`/`before_delete` listeners raise
  `MovimentacaoImutavelError`. Never hard-delete a product.
- [app/config.py](app/config.py) — settings from env vars: `APP_ENV` (dev/test/prod) and
  `DATABASE_URL`. [app/database.py](app/database.py) builds the engine from it (and enables
  SQLite foreign keys).
- [migrations/](migrations/) — Alembic. The app does NOT call `create_all`; schema changes need a
  migration (`alembic revision --autogenerate -m ...`). A test checks migrations match the models.
- Frontend: Tailwind classes in `app/templates/`; compiled CSS is committed at
  `app/static/css/tailwind.css` (config in `tailwind.config.js`). After changing template classes or
  colors run `make css` (needs Node). Do not reintroduce CDN links: the app must work offline.

## Tests

`tests/conftest.py` sets `APP_ENV=test` and a throwaway `DATABASE_URL` *before* importing `app`, and
each test gets its own SQLite file via `dependency_overrides`. The suite must never touch
`estoque.db`. Concurrency tests in `tests/test_servicos.py` use threads against a file DB.
