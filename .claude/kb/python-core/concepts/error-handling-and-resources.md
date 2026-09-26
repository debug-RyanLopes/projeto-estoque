# Tratamento de Erros e Recursos

## Nunca capturar exceção genérica silenciosamente

```python
# Errado — esconde qualquer bug, inclusive KeyboardInterrupt/SystemExit se for bare except
try:
    processa(item)
except:
    pass

# Errado — engole tudo, sem log, sem contexto
try:
    processa(item)
except Exception:
    pass

# Certo — captura o que se espera, deixa o resto propagar
try:
    processa(item)
except (ValueError, KeyError) as e:
    logger.warning("Falha ao processar %s: %s", item, e)
    raise  # ou trata e continua, mas nunca engole silenciosamente
```

Se realmente precisar capturar `Exception` de forma ampla (ex.: num loop de
processamento em lote onde um item ruim não deve derrubar os outros), sempre
logar e nunca usar `pass` sozinho.

## `with` para qualquer recurso que precisa ser liberado

```python
# Errado — se abrir() lançar exceção antes do close(), o arquivo vaza
f = open("dados.csv")
conteudo = f.read()
f.close()

# Certo
with open("dados.csv") as f:
    conteudo = f.read()
```

Vale para arquivos, conexões de banco, locks, sockets — qualquer coisa com
`__enter__`/`__exit__`. Múltiplos recursos:

```python
with open("entrada.csv") as entrada, open("saida.csv", "w") as saida:
    ...
```

## Context manager customizado

```python
from contextlib import contextmanager

@contextmanager
def conexao_banco(dsn: str):
    conn = criar_conexao(dsn)
    try:
        yield conn
    finally:
        conn.close()
```

Prefira `@contextmanager` a implementar `__enter__`/`__exit__` na mão quando a
lógica é simples (setup/teardown linear).

## Exceções customizadas: quando criar

```python
class EstoqueInsuficienteError(Exception):
    """Levantada quando uma retirada excede a quantidade disponível."""
    def __init__(self, produto: str, disponivel: int, solicitado: int):
        self.produto = produto
        self.disponivel = disponivel
        self.solicitado = solicitado
        super().__init__(
            f"{produto}: disponível {disponivel}, solicitado {solicitado}"
        )
```

Crie uma exceção customizada quando o chamador precisa distinguir esse erro de
outros `ValueError` genéricos para tratar de forma diferente. Não crie uma
hierarquia de exceções elaborada para um projeto pequeno — YAGNI se aplica aqui.

## `finally` vs `with`

Use `finally` só quando não há um context manager pronto e criar um seria
overkill para um único uso:

```python
lock.acquire()
try:
    ...
finally:
    lock.release()  # prefira lock.__enter__/__exit__ via `with lock:` quando disponível
```

## Erros de comparação que mascaram bugs

```python
# Comparação de float direta — quase sempre errado
if preco_total == 19.90:
    ...

# Correto
import math
if math.isclose(preco_total, 19.90, rel_tol=1e-9):
    ...
```

## Checklist rápido ao revisar tratamento de erros

- [ ] Nenhum `except:` bare ou `except Exception: pass` sem log.
- [ ] Toda abertura de recurso (arquivo, socket, conexão, lock) usa `with`.
- [ ] Exceções customizadas só onde o chamador realmente precisa diferenciar o erro.
- [ ] Mensagens de erro incluem contexto (qual item, qual valor) — não só "erro ocorreu".
- [ ] `raise` sem argumentos dentro de um `except` para repropagar preserva o traceback
      original — não recriar a exceção do zero.
