# Python Frameworks Quick Reference

> Fast lookup tables. Validação de dados: ver [pydantic/quick-reference.md](../pydantic/quick-reference.md).

## Como escolher um framework web

| Preciso de... | Escolha |
|---|---|
| API simples, alta performance, tipagem forte, async nativo | FastAPI |
| App pequeno/médio, controle explícito, poucas convenções impostas | Flask |
| Aplicação full-stack com admin pronto, ORM, autenticação, forms | Django |
| Só uma API interna consumida por outro serviço, sem UI | FastAPI |

Não misture padrões de dois frameworks no mesmo projeto sem motivo forte (ex.: usar
SQLAlchemy dentro de um projeto Django, que já tem seu próprio ORM) — cada framework
tem sua própria forma "certa" de fazer as coisas, e misturar aumenta a superfície de
bugs e a curva de aprendizado para quem mantém o código depois.

## Camada de dados: qual usar

| Preciso de... | Escolha |
|---|---|
| Validar/serializar dado externo (API, formulário, config) | Pydantic — [../pydantic/index.md](../pydantic/index.md) |
| ORM para banco relacional, fora do Django | SQLAlchemy — [patterns/sqlalchemy.md](patterns/sqlalchemy.md) |
| ORM para banco relacional, dentro de um projeto Django | Django ORM (nativo) — [patterns/django.md](patterns/django.md) |
| Manipulação/análise tabular (CSV, planilha, relatório) | pandas — [patterns/pandas.md](patterns/pandas.md) |

## Related Documentation

| Topic | Path |
|-------|------|
| Full Index | `index.md` |
| Pydantic (validação, oficial) | `../pydantic/index.md` |
| Python core (idiomas, oficial) | `../python/index.md` |
