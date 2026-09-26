# Type Hints

## Sintaxe básica e por versão

```python
# Python 3.9 e anteriores
from typing import List, Dict, Optional, Union

def busca(nomes: List[str]) -> Optional[Dict[str, int]]:
    ...

# Python 3.10+
def busca(nomes: list[str]) -> dict[str, int] | None:
    ...
```

**Antes de usar a sintaxe `X | Y` ou `list[str]` direto (sem importar de `typing`),
confirmar a versão mínima suportada do projeto** (`pyproject.toml` -> `requires-python`,
ou `setup.py`). Em 3.8/3.9 isso quebra em runtime sem `from __future__ import annotations`.

## `Optional` vs valor com default

```python
def cria_produto(nome: str, categoria: str | None = None) -> Produto:
    categoria = categoria or "geral"
    ...
```

`X | None` (ou `Optional[X]`) comunica que `None` é um valor válido e esperado — não é
só "posso não passar isso", é "a função lida explicitamente com ausência de valor".

## `Protocol`: tipagem estrutural

```python
from typing import Protocol

class TemNome(Protocol):
    nome: str

def imprime_nome(obj: TemNome) -> None:
    print(obj.nome)
```

Use `Protocol` quando quer aceitar "qualquer objeto com esse formato", sem forçar
herança de uma classe base comum — útil para desacoplar código de bibliotecas
externas ou para testes com duplos simples.

## `TypedDict`: tipar dicts com formato fixo

```python
from typing import TypedDict

class ProdutoDict(TypedDict):
    nome: str
    quantidade: int
    preco: float

def processa(dado: ProdutoDict) -> None:
    ...
```

Use quando o dado *precisa* continuar sendo um `dict` (ex.: vem de JSON/API) mas tem
formato conhecido — evita criar uma classe só para isso. Se o dado é criado e
manipulado dentro do próprio código, prefira `@dataclass`.

## Generics

```python
from typing import TypeVar, Generic

T = TypeVar("T")

class Pilha(Generic[T]):
    def __init__(self) -> None:
        self._itens: list[T] = []

    def empilha(self, item: T) -> None:
        self._itens.append(item)

    def desempilha(self) -> T:
        return self._itens.pop()
```

Python 3.12+ tem sintaxe nativa mais curta (`class Pilha[T]: ...`) — só usar se o
projeto já exige 3.12+.

## Quando tipar vale a pena (e quando não)

| Situação | Tipar? |
|---|---|
| Função pública / API de um módulo | Sim — é a documentação mais confiável que existe |
| Parâmetro cujo tipo já é óbvio pelo nome (`nome: str`) | Sim, ainda vale — ajuda IDE e `mypy` |
| Função privada de 3 linhas, uso local, tipo óbvio pelo contexto | Opcional — julgamento, não regra |
| Script descartável de uso único | Geralmente não compensa o esforço |
| Projeto já roda `mypy`/`pyright` no CI | Sempre tipar — senão o linter falha |

## Erro comum: tipar demais em detrimento de legibilidade

```python
# Exagerado para uso interno simples
def soma(a: int | float | complex, b: int | float | complex) -> int | float | complex:
    return a + b

# Suficiente
def soma(a: float, b: float) -> float:
    return a + b
```

`int` é aceito onde `float` é esperado por convenção de tipagem numérica em Python —
não precisa union para isso.
