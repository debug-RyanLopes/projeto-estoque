def test_cadastro_aparece_na_listagem(client):
    resp = client.post(
        "/produtos",
        data={
            "nome": "Parafuso M6",
            "sku": "PAR-M6",
            "preco_compra": "0.10",
            "preco_venda": "0.25",
            "estoque_minimo": "5",
        },
        follow_redirects=True,
    )

    assert resp.status_code == 200
    assert "Parafuso M6" in resp.text
    assert "PAR-M6" in resp.text


def test_sku_duplicado_e_rejeitado(client):
    client.post(
        "/produtos",
        data={
            "nome": "Parafuso M6",
            "sku": "PAR-M6",
            "preco_compra": "0.10",
            "preco_venda": "0.25",
            "estoque_minimo": "5",
        },
    )

    resp = client.post(
        "/produtos",
        data={
            "nome": "Parafuso M6 Duplicado",
            "sku": "PAR-M6",
            "preco_compra": "0.20",
            "preco_venda": "0.40",
            "estoque_minimo": "5",
        },
        follow_redirects=True,
    )

    assert "já cadastrado" in resp.text
    assert "Parafuso M6 Duplicado" not in resp.text
    assert resp.text.count(">Parafuso M6<") == 1


def test_exclusao_remove_produto(client):
    client.post(
        "/produtos",
        data={
            "nome": "Parafuso M6",
            "sku": "PAR-M6",
            "preco_compra": "0.10",
            "preco_venda": "0.25",
            "estoque_minimo": "5",
        },
    )

    resp = client.post("/produtos/1/excluir", follow_redirects=True)

    assert resp.status_code == 200
    assert "Nenhum produto cadastrado ainda." in resp.text  # some da tabela de produtos
    assert 'data-estoque=' not in resp.text


def _cadastrar(client, **extra):
    data = {
        "nome": "Parafuso M6", "sku": "PAR-M6",
        "preco_compra": "0.10", "preco_venda": "0.25", "estoque_minimo": "5",
    }
    data.update(extra)
    return client.post("/produtos", data=data, follow_redirects=True)


def test_cadastro_com_quantidade_inicial_define_saldo_e_registra_entrada(client):
    resp = _cadastrar(client, quantidade="12")

    assert 'data-estoque="ok"' in resp.text  # 12 > mínimo 5
    assert resp.text.count('data-tipo="entrada"') == 1
    assert "+12" in resp.text


def test_cadastro_sem_quantidade_inicial_comeca_zerado_e_sem_movimentacao(client):
    resp = _cadastrar(client)

    assert 'data-estoque="baixo"' in resp.text  # 0 <= mínimo 5
    assert 'data-tipo=' not in resp.text
    assert "Nenhuma movimentação registrada ainda." in resp.text


def test_quantidade_inicial_negativa_e_rejeitada(client):
    resp = client.post(
        "/produtos",
        data={"nome": "X", "sku": "X", "preco_compra": "1", "preco_venda": "2", "quantidade": "-3"},
    )

    assert resp.status_code == 422
