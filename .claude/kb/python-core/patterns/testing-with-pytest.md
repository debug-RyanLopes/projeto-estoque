# Testes com pytest

## Estrutura básica

```python
# test_estoque.py
def test_retirada_reduz_quantidade():
    produto = Produto(nome="Parafuso", quantidade=10)
    produto.retirar(3)
    assert produto.quantidade == 7


def test_retirada_maior_que_disponivel_levanta_erro():
    produto = Produto(nome="Parafuso", quantidade=5)
    with pytest.raises(EstoqueInsuficienteError):
        produto.retirar(10)
```

Nome de teste descreve o comportamento (`test_<ação>_<resultado_esperado>`), não a
implementação. Um `assert` por conceito testado — vários asserts relacionados ao
mesmo comportamento no mesmo teste são aceitáveis, comportamentos diferentes vão
em testes separados.

## Fixtures em vez de setup repetido

```python
import pytest

@pytest.fixture
def produto_com_estoque():
    return Produto(nome="Parafuso", quantidade=10)


def test_retirada(produto_com_estoque):
    produto_com_estoque.retirar(3)
    assert produto_com_estoque.quantidade == 7
```

Fixtures com `scope="module"`/`scope="session"` para setup caro (conexão de
banco de teste, servidor fake) que pode ser reutilizado entre testes — cuidado
com estado vazando entre testes quando o scope é maior que `"function"`.

## Parametrização em vez de duplicar o teste

```python
# Errado — três testes quase idênticos
def test_retirada_1():
    ...
def test_retirada_2():
    ...
def test_retirada_3():
    ...

# Certo
@pytest.mark.parametrize("quantidade_inicial, retirada, esperado", [
    (10, 3, 7),
    (5, 5, 0),
    (100, 1, 99),
])
def test_retirada(quantidade_inicial, retirada, esperado):
    produto = Produto(nome="X", quantidade=quantidade_inicial)
    produto.retirar(retirada)
    assert produto.quantidade == esperado
```

## Mocks: só onde há fronteira externa

```python
def test_notifica_estoque_baixo(mocker):
    envia_email = mocker.patch("estoque.notificacoes.envia_email")
    verifica_estoque_baixo(produto_com_1_unidade)
    envia_email.assert_called_once()
```

Mockar fronteiras externas (rede, email, banco, relógio) é correto. Mockar a
própria lógica de negócio que o teste deveria exercitar é um cheiro — geralmente
significa que o teste não está testando nada de verdade.

## Testes que dependem de tempo/relógio

```python
def test_produto_vencido(freezer):
    freezer.move_to("2026-01-01")
    produto = Produto(validade=date(2025, 12, 31))
    assert produto.vencido() is True
```

Usar uma lib de congelamento de tempo (`pytest-freezer`/`freezegun`) em vez de
`time.sleep()` ou datas relativas a `datetime.now()` no teste — testes que
dependem do relógio real do sistema são frágeis e ficam quebrando sozinhos.

## Checklist ao revisar testes

- [ ] Nome do teste descreve comportamento, não implementação.
- [ ] Sem duplicação óbvia que `@pytest.mark.parametrize` resolveria.
- [ ] Setup repetido virou fixture.
- [ ] Mock só em fronteira externa, nunca na lógica sob teste.
- [ ] Teste de erro usa `pytest.raises`, não `try/except` manual com `assert False`.
- [ ] Nenhum teste depende de ordem de execução ou de estado deixado por outro teste.
