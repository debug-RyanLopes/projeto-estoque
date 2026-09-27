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
    assert "Parafuso M6" not in resp.text
