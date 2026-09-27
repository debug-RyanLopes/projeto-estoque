from datetime import datetime

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Produto(Base):
    __tablename__ = "produtos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(200))
    sku: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    preco_compra: Mapped[float] = mapped_column(Numeric(10, 2))
    preco_venda: Mapped[float] = mapped_column(Numeric(10, 2))
    estoque_minimo: Mapped[int] = mapped_column(default=0)
    quantidade: Mapped[int] = mapped_column(default=0)

    movimentacoes: Mapped[list["Movimentacao"]] = relationship(
        back_populates="produto", cascade="all, delete-orphan"
    )


class Movimentacao(Base):
    __tablename__ = "movimentacoes"

    id: Mapped[int] = mapped_column(primary_key=True)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"))
    tipo: Mapped[str] = mapped_column(String(10))  # "entrada" ou "saida"
    quantidade: Mapped[int]
    data: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    produto: Mapped["Produto"] = relationship(back_populates="movimentacoes")
