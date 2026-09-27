"""FastAPI web app for stock control (cadastro, movimentação, alerta de estoque baixo)."""

from contextlib import asynccontextmanager
from typing import Annotated
from urllib.parse import quote

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import Movimentacao, Produto


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Controle de Estoque", lifespan=lifespan)
templates = Jinja2Templates(directory="app/templates")


def _redirect_com_erro(mensagem: str) -> RedirectResponse:
    return RedirectResponse(url=f"/?erro={quote(mensagem)}", status_code=303)


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, erro: str | None = None, db: Session = Depends(get_db)):
    produtos = db.query(Produto).order_by(Produto.nome).all()
    return templates.TemplateResponse(request, "index.html", {"produtos": produtos, "erro": erro})


@app.post("/produtos")
async def criar_produto(
    nome: Annotated[str, Form()],
    sku: Annotated[str, Form()],
    preco_compra: Annotated[float, Form(ge=0)],
    preco_venda: Annotated[float, Form(ge=0)],
    estoque_minimo: Annotated[int, Form(ge=0)] = 0,
    db: Session = Depends(get_db),
):
    if db.query(Produto).filter(Produto.sku == sku).first():
        return _redirect_com_erro(f"SKU '{sku}' já cadastrado")

    produto = Produto(
        nome=nome,
        sku=sku,
        preco_compra=preco_compra,
        preco_venda=preco_venda,
        estoque_minimo=estoque_minimo,
        quantidade=0,
    )
    db.add(produto)
    db.commit()
    return RedirectResponse(url="/", status_code=303)


@app.post("/produtos/{produto_id}/excluir")
async def excluir_produto(produto_id: int, db: Session = Depends(get_db)):
    produto = db.get(Produto, produto_id)
    if produto is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    db.delete(produto)
    db.commit()
    return RedirectResponse(url="/", status_code=303)


@app.post("/movimentacoes")
async def registrar_movimentacao(
    produto_id: Annotated[int, Form()],
    tipo: Annotated[str, Form()],
    quantidade: Annotated[int, Form(gt=0)],
    db: Session = Depends(get_db),
):
    produto = db.get(Produto, produto_id)
    if produto is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    if tipo not in ("entrada", "saida"):
        return _redirect_com_erro("Tipo de movimentação inválido")
    if tipo == "saida" and quantidade > produto.quantidade:
        return _redirect_com_erro(
            f"Estoque insuficiente para '{produto.nome}' (disponível: {produto.quantidade})"
        )

    produto.quantidade += quantidade if tipo == "entrada" else -quantidade
    db.add(Movimentacao(produto_id=produto_id, tipo=tipo, quantidade=quantidade))
    db.commit()
    return RedirectResponse(url="/", status_code=303)
