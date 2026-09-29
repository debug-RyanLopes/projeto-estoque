"""Regras de negócio do estoque, independentes de HTTP.

As rotas só traduzem requisição -> chamada de serviço -> resposta; toda a lógica
(e as decisões de concorrência) mora aqui.
"""

from decimal import Decimal

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .models import Movimentacao, Produto

TIPOS_MOVIMENTACAO = ("entrada", "saida")


class EstoqueError(Exception):
    """Erro de regra de negócio; a mensagem é segura para mostrar ao usuário."""


class ProdutoNaoEncontradoError(EstoqueError):
    def __init__(self) -> None:
        super().__init__("Produto não encontrado")


class SkuDuplicadoError(EstoqueError):
    def __init__(self, sku: str) -> None:
        super().__init__(f"SKU '{sku}' já cadastrado")


class TipoMovimentacaoInvalidoError(EstoqueError):
    def __init__(self) -> None:
        super().__init__("Tipo de movimentação inválido")


class EstoqueInsuficienteError(EstoqueError):
    def __init__(self, nome: str, disponivel: int) -> None:
        super().__init__(f"Estoque insuficiente para '{nome}' (disponível: {disponivel})")
        self.disponivel = disponivel


def listar_produtos(db: Session) -> list[Produto]:
    return list(db.scalars(select(Produto).where(Produto.ativo.is_(True)).order_by(Produto.nome)))


def criar_produto(
    db: Session,
    *,
    nome: str,
    sku: str,
    preco_compra: float | Decimal,
    preco_venda: float | Decimal,
    estoque_minimo: int = 0,
) -> Produto:
    """Cria o produto confiando na constraint UNIQUE do banco para o SKU.

    Não fazemos "SELECT antes, INSERT depois": entre os dois, outra requisição
    poderia inserir o mesmo SKU (TOCTOU). Inserimos direto e tratamos o erro.
    """
    produto = Produto(
        nome=nome,
        sku=sku,
        preco_compra=preco_compra,
        preco_venda=preco_venda,
        estoque_minimo=estoque_minimo,
        quantidade=0,
    )
    db.add(produto)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise SkuDuplicadoError(sku) from exc
    return produto


def excluir_produto(db: Session, produto_id: int) -> None:
    """Exclusão lógica: preserva o histórico de movimentações do produto."""
    result = db.execute(
        update(Produto).where(Produto.id == produto_id, Produto.ativo.is_(True)).values(ativo=False)
    )
    if result.rowcount == 0:
        db.rollback()
        raise ProdutoNaoEncontradoError()
    db.commit()


def registrar_movimentacao(db: Session, produto_id: int, tipo: str, quantidade: int) -> None:
    """Atualiza o saldo e grava a movimentação na mesma transação.

    O saldo é alterado por um único UPDATE condicional no banco
    (`quantidade = quantidade + delta`, com `AND quantidade >= q` nas saídas),
    em vez de ler o valor no Python, somar e gravar de volta. Assim, duas saídas
    simultâneas nunca "enxergam" o mesmo saldo antigo (lost update) nem deixam o
    estoque negativo.
    """
    if tipo not in TIPOS_MOVIMENTACAO:
        raise TipoMovimentacaoInvalidoError()

    delta = quantidade if tipo == "entrada" else -quantidade
    stmt = (
        update(Produto)
        .where(Produto.id == produto_id, Produto.ativo.is_(True))
        .values(quantidade=Produto.quantidade + delta)
    )
    if tipo == "saida":
        stmt = stmt.where(Produto.quantidade >= quantidade)

    if db.execute(stmt).rowcount == 0:
        # Ninguém foi atualizado: ou o produto não existe, ou faltou saldo.
        db.rollback()
        produto = db.execute(
            select(Produto.nome, Produto.quantidade).where(
                Produto.id == produto_id, Produto.ativo.is_(True)
            )
        ).first()
        if produto is None:
            raise ProdutoNaoEncontradoError()
        raise EstoqueInsuficienteError(produto.nome, produto.quantidade)

    db.add(Movimentacao(produto_id=produto_id, tipo=tipo, quantidade=quantidade))
    db.commit()
