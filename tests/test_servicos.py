"""Testes da camada de serviço: concorrência, histórico imutável e exclusão lógica."""

import threading

import pytest
from sqlalchemy import func, select

from app import services
from app.models import Movimentacao, MovimentacaoImutavelError, Produto


def _novo_produto(db, sku="PAR-M6", **extra):
    return services.criar_produto(
        db, nome="Parafuso M6", sku=sku, preco_compra=0.10, preco_venda=0.25, **extra
    )


def _rodar_em_paralelo(session_factory, n, tarefa):
    """Roda `tarefa(session)` em n threads ao mesmo tempo; devolve os resultados/erros."""
    largada = threading.Barrier(n)
    resultados = []

    def worker():
        with session_factory() as session:
            largada.wait()
            try:
                resultados.append(tarefa(session))
            except Exception as exc:  # noqa: BLE001 - o teste inspeciona o tipo
                resultados.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return resultados


def test_saidas_simultaneas_nunca_deixam_estoque_negativo(session_factory, db):
    produto_id = _novo_produto(db).id  # lido aqui: sessões não podem ser compartilhadas entre threads
    services.registrar_movimentacao(db, produto_id, "entrada", 10)

    # 8 saídas de 5 unidades disputando 10 em estoque: só 2 podem vencer.
    resultados = _rodar_em_paralelo(
        session_factory, 8, lambda s: services.registrar_movimentacao(s, produto_id, "saida", 5)
    )

    erros = [r for r in resultados if isinstance(r, Exception)]
    assert len(erros) == 6
    assert all(isinstance(e, services.EstoqueInsuficienteError) for e in erros)

    db.expire_all()
    assert db.get(Produto, produto_id).quantidade == 0
    saidas = db.scalar(select(func.count()).select_from(Movimentacao).where(Movimentacao.tipo == "saida"))
    assert saidas == 2


def test_cadastro_simultaneo_do_mesmo_sku_gera_um_unico_produto(session_factory, db):
    resultados = _rodar_em_paralelo(session_factory, 8, lambda s: _novo_produto(s))

    erros = [r for r in resultados if isinstance(r, Exception)]
    assert len(erros) == 7
    # Nenhum erro cru de banco vaza: todos viram o erro de negócio.
    assert all(isinstance(e, services.SkuDuplicadoError) for e in erros)
    assert db.scalar(select(func.count()).select_from(Produto)) == 1


def test_sku_duplicado_via_constraint_deixa_sessao_utilizavel(db):
    _novo_produto(db)

    with pytest.raises(services.SkuDuplicadoError):
        _novo_produto(db)

    # Após o rollback a mesma sessão continua funcionando.
    _novo_produto(db, sku="OUTRO")
    assert len(services.listar_produtos(db)) == 2


def test_movimentacao_nao_pode_ser_alterada_nem_apagada(db):
    produto = _novo_produto(db)
    services.registrar_movimentacao(db, produto.id, "entrada", 3)
    mov = db.scalars(select(Movimentacao)).one()

    mov.quantidade = 999
    with pytest.raises(MovimentacaoImutavelError):
        db.commit()
    db.rollback()

    db.delete(db.scalars(select(Movimentacao)).one())
    with pytest.raises(MovimentacaoImutavelError):
        db.commit()
    db.rollback()

    assert db.scalars(select(Movimentacao)).one().quantidade == 3


def test_excluir_produto_preserva_historico(db):
    produto = _novo_produto(db)
    services.registrar_movimentacao(db, produto.id, "entrada", 3)

    services.excluir_produto(db, produto.id)

    assert services.listar_produtos(db) == []
    assert db.scalar(select(func.count()).select_from(Movimentacao)) == 1
    with pytest.raises(services.ProdutoNaoEncontradoError):
        services.registrar_movimentacao(db, produto.id, "entrada", 1)
    with pytest.raises(services.ProdutoNaoEncontradoError):
        services.excluir_produto(db, produto.id)


def test_tipo_invalido_e_rejeitado(db):
    produto = _novo_produto(db)
    with pytest.raises(services.TipoMovimentacaoInvalidoError):
        services.registrar_movimentacao(db, produto.id, "roubo", 1)
