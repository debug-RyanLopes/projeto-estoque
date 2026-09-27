# FastAPI

> **Purpose**: Padrões de API async com FastAPI — validação via Pydantic, injeção de
> dependência, lifecycle, tratamento de erros
> **MCP Validated:** not validated (no FastAPI-specific MCP used) — **source-verified 2026-09-26**
> against official docs (see note below)

> Verificado contra fastapi.tiangolo.com (tutorial + release notes + PyPI metadata) em
> 2026-09-26. FastAPI estável mais recente na data: **0.141.1**, exigindo
> **Pydantic >= 2.9.0** (não há suporte a Pydantic v1 nesta versão) e Python >= 3.10.
> Validação de dados em si é coberta pelo domínio [pydantic](../pydantic/index.md) —
> este arquivo cobre apenas o que é específico do FastAPI.

## Endpoint básico com validação automática

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class ProdutoIn(BaseModel):
    nome: str
    quantidade: int
    preco: float

class ProdutoOut(ProdutoIn):
    id: int

@app.post("/produtos", response_model=ProdutoOut)
async def cria_produto(produto: ProdutoIn) -> ProdutoOut:
    novo = salva_no_banco(produto)
    return novo
```

`response_model` garante que a resposta é filtrada/validada contra o schema —
mesmo que a função retorne campos extras internos, só o que está no modelo sai.
Isso é documentado como recurso de segurança, não só de forma: dados internos
(ex.: custo de compra que não deveria ir ao cliente) nunca vazam por engano.
Alternativa igualmente oficial: anotar o tipo de retorno da função (`-> ProdutoOut`)
com um modelo base do qual `ProdutoIn` herda, em vez de usar o parâmetro
`response_model` — dá o mesmo filtro e ainda ajuda editores/mypy. Use
`response_model` quando o tipo retornado pela função é diferente do anunciado
(ex.: função retorna um `dict` ou um objeto ORM em vez do modelo Pydantic).

## `Depends()` para injeção de dependência

```python
from fastapi import Depends

def get_db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

@app.get("/produtos/{produto_id}")
async def le_produto(produto_id: int, db: Session = Depends(get_db_session)):
    return db.get(Produto, produto_id)
```

`Depends()` com uma função geradora (`yield`) é o padrão para recursos que
precisam de cleanup (sessão de banco, cliente HTTP). Por padrão o FastAPI
executa o código após o `yield` (o `finally`) **depois que a resposta já foi
enviada ao cliente** — inclusive se a rota levantar uma exceção, que é
repassada para dentro do `try`/`except` da própria dependência. Se você
capturar a exceção com `except`, deve relançá-la (ou levantar um
`HTTPException`), nunca engolir silenciosamente.

Com SQLite especificamente, o `create_engine()` do SQLAlchemy precisa de
`connect_args={"check_same_thread": False}`, porque uma única requisição pode
usar mais de uma thread (dependências rodando em threadpool) — sem essa opção
o driver `sqlite3` recusa acesso de thread diferente da que abriu a conexão.
Ver [patterns/sqlalchemy.md](sqlalchemy.md) para o padrão completo de sessão.

## async vs sync nos endpoints

```python
# Endpoint async — use quando chama I/O async (banco async, httpx.AsyncClient)
@app.get("/produtos")
async def lista_produtos():
    return await busca_produtos_async()

# Endpoint sync — FastAPI roda em threadpool automaticamente, ok para I/O bloqueante
@app.get("/relatorio")
def gera_relatorio():
    return processa_com_pandas()  # biblioteca síncrona, sem problema
```

**Erro comum:** declarar `async def` e chamar código bloqueante síncrono dentro
(driver de banco síncrono, `requests`, `time.sleep`) — isso trava o event loop
para todas as outras requisições. Se a chamada é síncrona, declare o endpoint
como `def` (sem `async`) e deixe o FastAPI rodar em thread separada, ou troque
para uma biblioteca async equivalente. Na dúvida, use `def` simples — a
diferença de performance de declarar `async def` sem I/O é irrelevante
comparada ao risco de travar o event loop com I/O bloqueante escondido.

## Validação de query params e path params

```python
from typing import Annotated
from fastapi import Query

@app.get("/produtos")
async def lista(
    categoria: Annotated[str | None, Query(max_length=50)] = None,
    limite: Annotated[int, Query(ge=1, le=100)] = 20,
):
    ...
```

O estilo `Annotated[tipo, Query(...)]` é o recomendado atualmente pela
documentação oficial (em vez de `categoria: str | None = Query(default=None, ...)`):
o valor default do Python fica explícito e a função continua chamável fora do
FastAPI sem quebrar. O estilo antigo com `Query()` como valor default ainda
funciona, mas não é mais o exemplo recomendado nos docs.

## Startup/shutdown com `lifespan`

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)  # startup: garante que as tabelas existem
    yield
    # shutdown: fechar pools de conexão, etc., se necessário

app = FastAPI(lifespan=lifespan)
```

O parâmetro `lifespan` é a forma recomendada pelos docs oficiais para código de
startup/shutdown. O decorator antigo `@app.on_event("startup")` é
**marcado como deprecated** nos docs ("advanced/events") — se `lifespan` for
passado, os handlers de `on_event` deixam de ser chamados (é um ou outro,
nunca os dois). Atenção: o próprio tutorial oficial de "SQL Databases" ainda
mostra `@app.on_event("startup")` em alguns exemplos legados — prefira
`lifespan` em código novo mesmo assim.

## Tratamento de erros

```python
from fastapi import FastAPI, HTTPException

@app.get("/produtos/{produto_id}")
async def le_produto(produto_id: int):
    produto = busca(produto_id)
    if produto is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return produto
```

Para erros de domínio reutilizados em vários endpoints, um exception handler
global evita repetir o `try/except` em cada rota:

```python
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(EstoqueInsuficienteError)
async def handler_estoque_insuficiente(request: Request, exc: EstoqueInsuficienteError):
    return JSONResponse(status_code=409, content={"detail": str(exc)})
```

## Checklist ao revisar código FastAPI

- [ ] Todo endpoint que recebe corpo JSON usa um modelo Pydantic, não `dict` cru.
- [ ] `async def` só quando o corpo da função só chama código async; na dúvida, `def`.
- [ ] Recursos com cleanup (sessão de banco, cliente HTTP) usam `Depends` com `yield`.
- [ ] SQLite: engine criado com `check_same_thread=False`.
- [ ] Erros de domínio viram `HTTPException` ou exception handler — nunca vazam
      stack trace cru para o cliente.
- [ ] Código de startup/shutdown usa `lifespan`, não `@app.on_event` (deprecated).
- [ ] Query/path params com validação usam o estilo `Annotated[tipo, Query(...)]`.
