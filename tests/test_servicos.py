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
    assert db.scalar(select(func.count()).select_from(Movimentacao)) == 2  # entrada + exclusão
    with pytest.raises(services.ProdutoNaoEncontradoError):
        services.registrar_movimentacao(db, produto.id, "entrada", 1)
    with pytest.raises(services.ProdutoNaoEncontradoError):
        services.excluir_produto(db, produto.id)


def test_tipo_invalido_e_rejeitado(db):
    produto = _novo_produto(db)
    with pytest.raises(services.TipoMovimentacaoInvalidoError):
        services.registrar_movimentacao(db, produto.id, "roubo", 1)


def test_quantidade_inicial_gera_entrada_e_saldo_bate_com_historico(db):
    produto = _novo_produto(db, quantidade_inicial=8)
    services.registrar_movimentacao(db, produto.id, "saida", 3)

    movs = services.listar_movimentacoes(db)
    entradas = sum(m.quantidade for m in movs if m.tipo == "entrada")
    saidas = sum(m.quantidade for m in movs if m.tipo == "saida")

    assert (entradas, saidas) == (8, 3)
    assert db.get(Produto, produto.id).quantidade == entradas - saidas == 5


def test_sku_duplicado_com_quantidade_inicial_nao_deixa_movimentacao_orfa(db):
    _novo_produto(db, quantidade_inicial=5)

    with pytest.raises(services.SkuDuplicadoError):
        _novo_produto(db, quantidade_inicial=99)

    assert [m.quantidade for m in services.listar_movimentacoes(db)] == [5]


def test_exclusao_registra_saldo_e_nao_conta_no_balanco(db):
    produto = _novo_produto(db, quantidade_inicial=10)
    services.registrar_movimentacao(db, produto.id, "saida", 4)

    services.excluir_produto(db, produto.id)

    ultima = services.listar_movimentacoes(db)[0]
    assert (ultima.tipo, ultima.quantidade) == ("exclusao", 6)
    movs = services.listar_movimentacoes(db)
    entradas = sum(m.quantidade for m in movs if m.tipo == "entrada")
    saidas = sum(m.quantidade for m in movs if m.tipo == "saida")
    assert entradas - saidas == db.get(Produto, produto.id).quantidade == 6


def test_excluir_duas_vezes_registra_uma_unica_exclusao(db):
    produto = _novo_produto(db)
    services.excluir_produto(db, produto.id)

    with pytest.raises(services.ProdutoNaoEncontradoError):
        services.excluir_produto(db, produto.id)

    tipos = [m.tipo for m in services.listar_movimentacoes(db)]
    assert tipos == ["exclusao"]
