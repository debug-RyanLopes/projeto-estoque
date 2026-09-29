def test_saida_maior_que_estoque_e_rejeitada(client):
    client.post("/produtos", data={
        "nome": "Parafuso M6", "sku": "PAR-M6",
        "preco_compra": "0.10", "preco_venda": "0.25", "estoque_minimo": "5",
    })
    client.post("/movimentacoes", data={"produto_id": "1", "tipo": "entrada", "quantidade": "3"})

    resp = client.post(
        "/movimentacoes",
        data={"produto_id": "1", "tipo": "saida", "quantidade": "100"},
        follow_redirects=True,
    )

    assert "Estoque insuficiente" in resp.text
    assert "disponível: 3" in resp.text


def test_alerta_estoque_baixo_liga_desliga(client):
    client.post("/produtos", data={
        "nome": "Parafuso M6", "sku": "PAR-M6",
        "preco_compra": "0.10", "preco_venda": "0.25", "estoque_minimo": "5",
    })
    client.post("/movimentacoes", data={"produto_id": "1", "tipo": "entrada", "quantidade": "3"})

    resp_baixo = client.get("/")
    assert 'data-estoque="baixo"' in resp_baixo.text

    resp_ok = client.post(
        "/movimentacoes",
        data={"produto_id": "1", "tipo": "entrada", "quantidade": "10"},
        follow_redirects=True,
    )

    assert 'data-estoque="baixo"' not in resp_ok.text
    assert 'data-estoque="ok"' in resp_ok.text


def _produto_com_estoque(client, quantidade="10"):
    client.post("/produtos", data={
        "nome": "Parafuso M6", "sku": "PAR-M6", "quantidade": quantidade,
        "preco_compra": "0.10", "preco_venda": "0.25", "estoque_minimo": "5",
    })


def test_historico_lista_entradas_e_saidas(client):
    _produto_com_estoque(client, "10")  # entrada inicial de 10
    client.post("/movimentacoes", data={"produto_id": "1", "tipo": "entrada", "quantidade": "4"})
    resp = client.post(
        "/movimentacoes",
        data={"produto_id": "1", "tipo": "saida", "quantidade": "3"},
        follow_redirects=True,
    )

    assert "Registro de movimentações" in resp.text
    assert resp.text.count('data-tipo="entrada"') == 2
    assert resp.text.count('data-tipo="saida"') == 1
    assert "+10" in resp.text and "+4" in resp.text and "−3" in resp.text


def test_historico_mostra_mais_recente_primeiro(client):
    _produto_com_estoque(client, "10")
    resp = client.post(
        "/movimentacoes",
        data={"produto_id": "1", "tipo": "saida", "quantidade": "3"},
        follow_redirects=True,
    )

    assert resp.text.index('data-tipo="saida"') < resp.text.index('data-tipo="entrada"')


def test_saida_rejeitada_nao_aparece_no_historico(client):
    _produto_com_estoque(client, "3")
    resp = client.post(
        "/movimentacoes",
        data={"produto_id": "1", "tipo": "saida", "quantidade": "100"},
        follow_redirects=True,
    )

    assert 'data-tipo="saida"' not in resp.text


def test_historico_de_produto_excluido_continua_visivel(client):
    _produto_com_estoque(client, "10")

    resp = client.post("/produtos/1/excluir", follow_redirects=True)

    assert 'data-tipo="entrada"' in resp.text
    assert "excluído" in resp.text


def test_exclusao_de_produto_aparece_no_historico(client):
    _produto_com_estoque(client, "10")
    client.post("/movimentacoes", data={"produto_id": "1", "tipo": "saida", "quantidade": "4"})

    resp = client.post("/produtos/1/excluir", follow_redirects=True)

    assert resp.text.count('data-tipo="exclusao"') == 1
    assert "Produto excluído" in resp.text
    assert "6 un. em estoque" in resp.text
    # é o registro mais recente, então aparece antes da entrada inicial
    assert resp.text.index('data-tipo="exclusao"') < resp.text.index('data-tipo="entrada"')


def test_excluir_produto_inexistente_nao_registra_nada(client):
    resp = client.post("/produtos/99/excluir", follow_redirects=True)

    assert resp.status_code == 404
