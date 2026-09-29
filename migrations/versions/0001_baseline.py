"""Baseline: tabelas produtos e movimentacoes

Revision ID: 0001
Revises:
Create Date: 2026-09-29
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Bancos criados pela versão antiga (Base.metadata.create_all) já têm estas
    # tabelas; nesse caso não recriamos nada e o Alembic só passa a controlá-las.
    existentes = set(sa.inspect(op.get_bind()).get_table_names())

    if "produtos" not in existentes:
        op.create_table(
            "produtos",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("nome", sa.String(200), nullable=False),
            sa.Column("sku", sa.String(50), nullable=False),
            sa.Column("preco_compra", sa.Numeric(10, 2), nullable=False),
            sa.Column("preco_venda", sa.Numeric(10, 2), nullable=False),
            sa.Column("estoque_minimo", sa.Integer(), nullable=False),
            sa.Column("quantidade", sa.Integer(), nullable=False),
        )
        op.create_index("ix_produtos_sku", "produtos", ["sku"], unique=True)

    if "movimentacoes" not in existentes:
        op.create_table(
            "movimentacoes",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("produto_id", sa.Integer(), sa.ForeignKey("produtos.id"), nullable=False),
            sa.Column("tipo", sa.String(10), nullable=False),
            sa.Column("quantidade", sa.Integer(), nullable=False),
            sa.Column("data", sa.DateTime(), nullable=False),
        )


def downgrade() -> None:
    op.drop_table("movimentacoes")
    op.drop_index("ix_produtos_sku", table_name="produtos")
    op.drop_table("produtos")
