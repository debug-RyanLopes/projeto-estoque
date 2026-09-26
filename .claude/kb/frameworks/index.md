# Frameworks — Índice

> Domínio: frameworks web e de dados usados sobre Python. Cada arquivo em `patterns/`
> é autocontido — carregar só o que a tarefa exige. Não cobre Python core — ver
> [../python-core/index.md](../python-core/index.md).

## Quick reference

- [quick-reference.md](quick-reference.md) — tabela de decisão (qual framework web,
  qual camada de dados) para consulta rápida.

## Patterns

- [patterns/fastapi.md](patterns/fastapi.md) — API async, validação via Pydantic,
  `Depends()`, docs automáticas.
- [patterns/flask.md](patterns/flask.md) — micro-framework sync, blueprints, validação
  manual de entrada.
- [patterns/django.md](patterns/django.md) — full-stack (ORM, admin, forms), convenção
  sobre configuração.
- [patterns/sqlalchemy.md](patterns/sqlalchemy.md) — ORM/Core 2.0-style, sessions,
  queries com `select()`.
- [patterns/pydantic.md](patterns/pydantic.md) — validação e serialização de dados (v2).
- [patterns/pandas.md](patterns/pandas.md) — manipulação tabular, armadilhas de
  performance comuns.
