from datetime import datetime, timezone

from sqlalchemy import Boolean, ForeignKey, Numeric, String, event, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def _agora_utc() -> datetime:
    return datetime.now(timezone.utc)


class Produto(Base):
    __tablename__ = "produtos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(200))
    sku: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    preco_compra: Mapped[float] = mapped_column(Numeric(10, 2))
    preco_venda: Mapped[float] = mapped_column(Numeric(10, 2))
    estoque_minimo: Mapped[int] = mapped_column(default=0)
    quantidade: Mapped[int] = mapped_column(default=0)
    # Exclusão lógica: o produto some da tela, mas o histórico de movimentações fica.
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())

    movimentacoes: Mapped[list["Movimentacao"]] = relationship(back_populates="produto")


class Movimentacao(Base):
    """Registro imutável: uma vez gravada, nunca é alterada nem apagada.

    tipo: "entrada" e "saida" mexem no saldo; "exclusao" só registra que o produto foi
    excluído (quantidade = saldo que ele tinha) e NÃO entra na conta entradas - saídas.
    """

    __tablename__ = "movimentacoes"

    id: Mapped[int] = mapped_column(primary_key=True)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"))
    tipo: Mapped[str] = mapped_column(String(10))  # "entrada", "saida" ou "exclusao"
    quantidade: Mapped[int]
    data: Mapped[datetime] = mapped_column(default=_agora_utc)

    produto: Mapped["Produto"] = relationship(back_populates="movimentacoes")


class MovimentacaoImutavelError(Exception):
    pass


@event.listens_for(Movimentacao, "before_update")
@event.listens_for(Movimentacao, "before_delete")
def _bloquear_alteracao_de_movimentacao(mapper, connection, target):
    raise MovimentacaoImutavelError(
        "Movimentações são um histórico imutável; registre uma nova movimentação de ajuste."
    )
