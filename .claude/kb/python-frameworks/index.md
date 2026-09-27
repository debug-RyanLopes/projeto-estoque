# Python Frameworks Knowledge Base

> **Purpose**: Web e ORM frameworks sobre Python sem cobertura própria no KB do
> AgentSpec — FastAPI, Flask, Django, SQLAlchemy, pandas.
> **MCP Validated:** not validated (hand-authored — see note below)

> Validação de dados fica no domínio [pydantic](../pydantic/index.md), já registrado
> e mantido pelo plugin — este domínio não duplica esse conteúdo. Idiomas Python
> puros (dataclasses, generators, type hints) ficam em [python](../python/index.md).

## Quick Navigation

### Patterns (< 200 lines each)

| File | Purpose |
|------|---------|
| [patterns/fastapi.md](patterns/fastapi.md) | API async, `Depends()`, validação via Pydantic, docs automáticas |
| [patterns/flask.md](patterns/flask.md) | Micro-framework sync, blueprints, validação manual de entrada |
| [patterns/django.md](patterns/django.md) | Full-stack (ORM, admin, forms), N+1, migrations |
| [patterns/sqlalchemy.md](patterns/sqlalchemy.md) | ORM/Core 2.0-style, sessions, queries com `select()` |
| [patterns/pandas.md](patterns/pandas.md) | Manipulação tabular, vetorização, armadilhas de performance |

---

## Quick Reference

- [quick-reference.md](quick-reference.md) — tabela de decisão (qual framework web,
  qual camada de dados) para consulta rápida.

---

## Nota sobre validação

Este domínio foi escrito à mão, sem o passo de fact-check adversarial + validação MCP
que os domínios oficiais do plugin passam (ver `kb-build`/`kb-architect`). Trate como
referência de boa-fé, não como conteúdo com a mesma barra de confiança dos demais
domínios registrados em `_index.yaml`. Para elevar ao mesmo padrão, rodar
`/create-kb python-frameworks --validated`.

---

## Agent Usage

| Agent | Primary Files | Use Case |
|-------|---------------|----------|
| python-developer | patterns/fastapi.md, patterns/sqlalchemy.md | Escrever código de API/ORM |
| code-reviewer | qualquer pattern relevante ao arquivo revisado | Revisar uso de framework web/ORM |
