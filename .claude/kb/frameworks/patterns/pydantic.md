# Pydantic (v2)

> Pydantic v2 mudou nomes de método em relação à v1 (`model_validate` em vez de
> `parse_obj`, `model_dump` em vez de `dict()`, `ConfigDict` em vez de classe
> `Config`). Confirmar a versão instalada (`pip show pydantic`) antes de aplicar
> os exemplos abaixo — projeto em v1 usa a API antiga.

## Modelo básico e validação

```python
from pydantic import BaseModel, Field, field_validator

class Produto(BaseModel):
    nome: str = Field(min_length=1, max_length=200)
    quantidade: int = Field(ge=0)
    preco: float = Field(gt=0)

    @field_validator("nome")
    @classmethod
    def nome_sem_espacos_nas_pontas(cls, v: str) -> str:
        return v.strip()
```

```python
# Validar dado externo (dict/JSON) -> instância
produto = Produto.model_validate({"nome": " Parafuso ", "quantidade": 10, "preco": 0.5})

# Serializar de volta
produto.model_dump()        # -> dict
produto.model_dump_json()   # -> string JSON
```

## `v1` vs `v2` — tabela de migração rápida

| v1 | v2 |
|---|---|
| `Produto.parse_obj(dado)` | `Produto.model_validate(dado)` |
| `produto.dict()` | `produto.model_dump()` |
| `produto.json()` | `produto.model_dump_json()` |
| `class Config: orm_mode = True` | `model_config = ConfigDict(from_attributes=True)` |
| `@validator` | `@field_validator` |

## Validação entre campos (model-level)

```python
from pydantic import BaseModel, model_validator

class Retirada(BaseModel):
    quantidade_disponivel: int
    quantidade_solicitada: int

    @model_validator(mode="after")
    def checa_disponibilidade(self) -> "Retirada":
        if self.quantidade_solicitada > self.quantidade_disponivel:
            raise ValueError("quantidade solicitada maior que a disponível")
        return self
```

## Ler modelo a partir de objeto ORM (ex.: instância SQLAlchemy)

```python
class ProdutoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    quantidade: int

# produto_orm é uma instância de modelo SQLAlchemy, não um dict
saida = ProdutoOut.model_validate(produto_orm)
```

`from_attributes=True` (antigo `orm_mode`) permite validar a partir de um
objeto com atributos, não só de um dict — essencial para converter modelos
ORM em schemas de resposta de API.

## Erro comum: usar Pydantic só para tipar, ignorando a validação

```python
# Errado — cria o modelo sem passar pela validação (bypassa Field(ge=0), etc.)
produto = Produto.model_construct(nome="X", quantidade=-5, preco=0)

# Certo — sempre validar dado que vem de fora
produto = Produto.model_validate(dado_externo)
```

`model_construct` pula validação (usado internamente para performance em casos
muito específicos) — não é a forma normal de criar um modelo a partir de dado
não confiável.

## Checklist ao revisar código Pydantic

- [ ] Confirma se o projeto está em v1 ou v2 antes de sugerir `model_validate`/`.dict()`.
- [ ] Campos numéricos com regra de negócio (`ge=0`, `gt=0`) usam `Field(...)`, não
      validação manual depois de criar o objeto.
- [ ] Validação entre campos usa `@model_validator`, não lógica solta fora do modelo.
- [ ] Dado externo (API, formulário) sempre passa por `model_validate`, nunca
      `model_construct` ou instanciação direta sem validação.
