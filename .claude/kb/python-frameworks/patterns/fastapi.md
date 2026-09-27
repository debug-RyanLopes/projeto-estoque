# FastAPI

> **Purpose**: Padrões de API async com FastAPI — validação via Pydantic, injeção de
> dependência, tratamento de erros
> **MCP Validated:** not validated (hand-authored)

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
precisam de cleanup (sessão de banco, cliente HTTP) — o FastAPI chama o código
após o `yield` automaticamente ao final da requisição, mesmo se houver erro.

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
para uma biblioteca async equivalente.

## Validação de query params e path params

```python
from fastapi import Query

@app.get("/produtos")
async def lista(
    categoria: str | None = Query(default=None, max_length=50),
    limite: int = Query(default=20, ge=1, le=100),
):
    ...
```

## Tratamento de erros

```python
from fastapi import HTTPException

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
@app.exception_handler(EstoqueInsuficienteError)
async def handler_estoque_insuficiente(request, exc: EstoqueInsuficienteError):
    return JSONResponse(status_code=409, content={"detail": str(exc)})
```

## Checklist ao revisar código FastAPI

- [ ] Todo endpoint que recebe corpo JSON usa um modelo Pydantic, não `dict` cru.
- [ ] `async def` só quando o corpo da função só chama código async.
- [ ] Recursos com cleanup (sessão de banco, cliente HTTP) usam `Depends` com `yield`.
- [ ] Erros de domínio viram `HTTPException` ou exception handler — nunca vazam
      stack trace cru para o cliente.
