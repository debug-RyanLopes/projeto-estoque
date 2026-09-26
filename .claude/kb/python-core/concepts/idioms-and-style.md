# Idiomas e Estilo Pythônico

## Comprehensions vs loop explícito

```python
# Não idiomático
resultado = []
for x in itens:
    if x.ativo:
        resultado.append(x.nome)

# Idiomático
resultado = [x.nome for x in itens if x.ativo]
```

Use comprehension quando cabe em ~1-2 linhas legíveis. Se a lógica interna precisar de
múltiplas condições ou efeitos colaterais, prefira o loop explícito — comprehension
ilegível é pior que loop claro.

## `enumerate` e `zip`

```python
# Não idiomático
for i in range(len(produtos)):
    print(i, produtos[i])

# Idiomático
for i, produto in enumerate(produtos):
    print(i, produto)

# Duas listas em paralelo
for produto, quantidade in zip(produtos, quantidades):
    ...
```

## Construção de strings

```python
# Não idiomático — O(n²) em loop grande, cada += cria uma nova string
texto = ""
for parte in partes:
    texto += parte

# Idiomático
texto = "".join(partes)

# f-strings em vez de % ou .format()
mensagem = f"Produto {nome} tem {quantidade} unidades"
```

## `pathlib` em vez de `os.path`

```python
# Não idiomático
import os
caminho = os.path.join(base, "dados", "estoque.csv")
if os.path.exists(caminho):
    ...

# Idiomático
from pathlib import Path
caminho = Path(base) / "dados" / "estoque.csv"
if caminho.exists():
    ...
```

`Path` compõe com `/`, tem `.read_text()`/`.write_text()`, `.glob()`, e funciona igual em
Windows/Linux — evita bugs de separador de caminho.

## `enum` em vez de valores mágicos

```python
# Não idiomático
STATUS_ATIVO = 1
STATUS_INATIVO = 2

def processa(status):
    if status == 1:
        ...

# Idiomático
from enum import Enum

class Status(Enum):
    ATIVO = "ativo"
    INATIVO = "inativo"

def processa(status: Status):
    if status == Status.ATIVO:
        ...
```

Torna valores inválidos impossíveis de passar sem erro, e o IDE autocompleta as opções.

## `dataclasses` em vez de classes manuais

```python
# Não idiomático
class Produto:
    def __init__(self, nome, quantidade, preco):
        self.nome = nome
        self.quantidade = quantidade
        self.preco = preco

# Idiomático
from dataclasses import dataclass

@dataclass
class Produto:
    nome: str
    quantidade: int
    preco: float
```

`@dataclass` gera `__init__`, `__repr__` e `__eq__` automaticamente. Use
`@dataclass(frozen=True)` para imutabilidade, `@dataclass(slots=True)` (3.10+) para
reduzir uso de memória em coleções grandes de instâncias.

## Comparações que parecem certas mas não são

```python
if x == True:      # -> if x:
if x == None:       # -> if x is None:
if len(lista) == 0:  # -> if not lista:
if tipo == "a" or tipo == "b" or tipo == "c":  # -> if tipo in {"a", "b", "c"}:
```

## Quando NÃO aplicar um idioma

- Não force comprehensions aninhadas de 3+ níveis — vira ilegível; use loop com nomes claros.
- Não troque `dict` simples por `dataclass` se o dado nunca sai daquela função — overhead
  sem ganho.
- Não substitua `if/elif` claro por truques de dispatch table só por "ser mais Pythônico" —
  legibilidade primeiro.
