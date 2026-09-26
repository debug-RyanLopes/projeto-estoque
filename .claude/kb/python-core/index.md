# Python Core — Índice

> Domínio: idiomas da linguagem, tipagem, tratamento de erros/recursos, concorrência,
> performance, testes e empacotamento. Não cobre frameworks — ver
> [../frameworks/index.md](../frameworks/index.md).

## Quick reference

- [quick-reference.md](quick-reference.md) — tabela de decisão para escolhas comuns
  (list vs gerador, dataclass vs dict vs namedtuple, sync vs async, etc.)

## Concepts

- [concepts/idioms-and-style.md](concepts/idioms-and-style.md) — trocas idiomáticas comuns,
  comprehensions, f-strings, `pathlib`, `enum`, `dataclasses`.
- [concepts/typing.md](concepts/typing.md) — type hints, `Protocol`, generics, `TypedDict`,
  quando tipar vale a pena.
- [concepts/error-handling-and-resources.md](concepts/error-handling-and-resources.md) —
  exceções, `with`/context managers, erros comuns que vazam recursos.
- [concepts/concurrency-and-performance.md](concepts/concurrency-and-performance.md) —
  threading vs multiprocessing vs asyncio, GIL, perfilamento, otimizações que importam.

## Patterns

- [patterns/testing-with-pytest.md](patterns/testing-with-pytest.md) — estrutura de testes,
  fixtures, parametrização, mocks.
- [patterns/packaging-and-project-layout.md](patterns/packaging-and-project-layout.md) —
  `pyproject.toml`, layout `src/`, ambientes virtuais, linters/formatters.
