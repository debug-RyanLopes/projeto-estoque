"""FastAPI web app for stock control (cadastro, movimentação, alerta de estoque baixo).

As rotas são `def` (síncronas) de propósito: o SQLAlchemy usado aqui é síncrono, e o
FastAPI executa rotas `def` num pool de threads, sem travar o event loop. Uma rota
`async def` que chamasse o banco síncrono bloquearia o servidor inteiro durante a query.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated
from urllib.parse import quote

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from . import services
from .database import get_db

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Controle de Estoque")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def _data_local(valor: datetime) -> str:
    """As datas são gravadas em UTC; mostramos no fuso do computador que roda o app."""
    return valor.replace(tzinfo=timezone.utc).astimezone().strftime("%d/%m/%Y %H:%M")


templates.env.filters["data_local"] = _data_local


def _redirect_com_erro(mensagem: str) -> RedirectResponse:
    return RedirectResponse(url=f"/?erro={quote(mensagem)}", status_code=303)


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, erro: str | None = None, db: Session = Depends(get_db)):
    context = {
        "produtos": services.listar_produtos(db),
        "movimentacoes": services.listar_movimentacoes(db),
        "erro": erro,
    }
    return templates.TemplateResponse(request, "index.html", context)


@app.post("/produtos")
def criar_produto(
    nome: Annotated[str, Form()],
    sku: Annotated[str, Form()],
    preco_compra: Annotated[float, Form(ge=0)],
    preco_venda: Annotated[float, Form(ge=0)],
    estoque_minimo: Annotated[int, Form(ge=0)] = 0,
    quantidade: Annotated[int, Form(ge=0)] = 0,
    db: Session = Depends(get_db),
):
    try:
        services.criar_produto(
            db,
            nome=nome,
            sku=sku,
            preco_compra=preco_compra,
            preco_venda=preco_venda,
            estoque_minimo=estoque_minimo,
            quantidade_inicial=quantidade,
        )
    except services.SkuDuplicadoError as exc:
        return _redirect_com_erro(str(exc))
    return RedirectResponse(url="/", status_code=303)


@app.post("/produtos/{produto_id}/excluir")
def excluir_produto(produto_id: int, db: Session = Depends(get_db)):
    try:
        services.excluir_produto(db, produto_id)
    except services.ProdutoNaoEncontradoError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return RedirectResponse(url="/", status_code=303)


@app.post("/movimentacoes")
def registrar_movimentacao(
    produto_id: Annotated[int, Form()],
    tipo: Annotated[str, Form()],
    quantidade: Annotated[int, Form(gt=0)],
    db: Session = Depends(get_db),
):
    try:
        services.registrar_movimentacao(db, produto_id, tipo, quantidade)
    except services.ProdutoNaoEncontradoError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except services.EstoqueError as exc:
        return _redirect_com_erro(str(exc))
    return RedirectResponse(url="/", status_code=303)
