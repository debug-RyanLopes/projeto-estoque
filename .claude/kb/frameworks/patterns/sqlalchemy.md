# SQLAlchemy (2.0-style)

> Este arquivo assume o estilo 2.0 (`Session` + `select()`), atual desde
> SQLAlchemy 1.4+ e obrigatório em 2.0. Projetos antigos em `Query()`-style
> (`session.query(Model).filter(...)`) ainda funcionam mas são o estilo legado —
> não misturar os dois estilos no mesmo projeto sem motivo.

## Modelos declarativos

```python
from sqlalchemy import String, Numeric
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class Produto(Base):
    __tablename__ = "produtos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(200))
    quantidade: Mapped[int] = mapped_column(default=0)
    preco: Mapped[float] = mapped_column(Numeric(10, 2))
```

`Mapped[tipo]` + `mapped_column()` é o padrão 2.0 — dá tipagem estática real
(mypy/pyright entendem o tipo da coluna), diferente do `Column(Integer)` antigo.

## Sessão: sempre com `with` (ou `Depends` com `yield` num framework web)

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

engine = create_engine("postgresql://...")

with Session(engine) as session:
    produto = Produto(nome="Parafuso", quantidade=100, preco=0.50)
    session.add(produto)
    session.commit()
```

Nunca criar uma `Session` global reutilizada entre requisições/threads sem
scoped session — `Session` não é thread-safe.

## Queries com `select()`

```python
from sqlalchemy import select

with Session(engine) as session:
    stmt = select(Produto).where(Produto.quantidade < 10)
    produtos_baixo_estoque = session.scalars(stmt).all()

    # Uma linha só
    produto = session.scalars(
        select(Produto).where(Produto.nome == "Parafuso")
    ).first()
```

`session.scalars(stmt)` retorna as entidades diretamente; `session.execute(stmt)`
retorna `Row` (tuplas) — usar `scalars` quando o select é de uma única entidade.

## N+1 e eager loading

```python
from sqlalchemy.orm import selectinload, joinedload

# Errado — acessar .categoria em loop dispara 1 query por produto
produtos = session.scalars(select(Produto)).all()
for p in produtos:
    print(p.categoria.nome)

# Certo — selectinload para relação um-para-muitos/muitos-para-muitos
stmt = select(Produto).options(selectinload(Produto.categoria))

# joinedload para relação muitos-para-um/um-para-um (faz JOIN numa query só)
stmt = select(Produto).options(joinedload(Produto.categoria))
```

## Transações: commit explícito, rollback em erro

```python
try:
    with Session(engine) as session:
        produto = session.get(Produto, produto_id)
        produto.quantidade -= quantidade_retirada
        session.commit()
except Exception:
    session.rollback()
    raise
```

Com `with Session(...) as session:`, um erro não tratado já dispara rollback
automático ao sair do bloco — o `except`/`rollback` explícito só é necessário
se for capturar o erro para tratar e continuar usando a mesma sessão depois.

## Checklist ao revisar código SQLAlchemy

- [ ] Modelos usam `Mapped[]`/`mapped_column()` (2.0-style), não `Column()` puro
      misturado no mesmo projeto que já usa o estilo novo.
- [ ] Sessão sempre dentro de `with` ou gerenciada pelo framework (`Depends` com `yield`).
- [ ] Loop sobre resultado de query que acessa relação usa `selectinload`/`joinedload`.
- [ ] Nenhuma `Session` global compartilhada entre threads/requisições.
- [ ] Dinheiro em `Numeric`, nunca `Float`.
