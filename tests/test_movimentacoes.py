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
