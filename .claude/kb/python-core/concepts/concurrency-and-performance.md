# Concorrência e Performance

## O GIL em uma frase

O Global Interpreter Lock garante que só uma thread executa bytecode Python por vez
num processo. Isso significa: **threads não aceleram trabalho CPU-bound** em CPython
(o padrão); elas ajudam em trabalho I/O-bound porque o GIL é liberado durante espera
de I/O (rede, disco).

> Nota: builds "free-threaded" do CPython (3.13+, ainda experimental) removem o GIL
> opcionalmente — não assumir isso disponível a menos que o projeto declare
> explicitamente essa build.

## Qual modelo de concorrência usar

| Cenário | Ferramenta | Por quê |
|---|---|---|
| Muitas requisições de rede simultâneas | `asyncio` + cliente async (httpx, aiohttp) | Uma única thread lida com milhares de conexões esperando I/O |
| Poucas chamadas bloqueantes paralelas, código já síncrono | `concurrent.futures.ThreadPoolExecutor` | Simples de integrar sem reescrever tudo como async |
| Cálculo pesado de CPU (parsing, matemática, compressão) | `concurrent.futures.ProcessPoolExecutor` / `multiprocessing` | Cada processo tem seu próprio GIL — paralelismo real |
| Pipeline de dados com bibliotecas que já liberam o GIL (numpy, pandas em operações vetorizadas) | Threads às vezes bastam | Numpy/pandas liberam o GIL durante operações C internas |

## `asyncio`: erros comuns

```python
# Errado — chama função bloqueante dentro de código async, trava o event loop inteiro
async def busca_dados():
    resultado = requests.get(url)  # biblioteca síncrona!
    return resultado.json()

# Certo — usar um cliente async
async def busca_dados():
    async with httpx.AsyncClient() as client:
        resultado = await client.get(url)
        return resultado.json()
```

```python
# Errado — esquece de rodar as tarefas em paralelo
for url in urls:
    resultado = await busca(url)  # sequencial, uma de cada vez

# Certo — dispara todas e espera juntas
resultados = await asyncio.gather(*(busca(url) for url in urls))
```

Se precisar chamar código síncrono bloqueante dentro de uma função async sem
alternativa async, use `asyncio.to_thread(func, *args)` (3.9+) em vez de chamar
direto.

## Performance: onde otimizar primeiro

1. **Meça antes de otimizar.** `cProfile` ou `python -m timeit` para trechos
   isolados. Não reescreva código "porque parece lento" sem dado.
2. **Complexidade algorítmica primeiro.** Trocar uma busca O(n) em lista por
   lookup O(1) em `set`/`dict` costuma valer mais que qualquer microotimização.
3. **Evite recomputar.** `functools.lru_cache`/`functools.cache` para funções
   puras chamadas repetidamente com os mesmos argumentos.
4. **Evite cópias desnecessárias** de estruturas grandes — fatiar uma lista
   grande (`lista[:]`) ou concatenar DataFrames em loop custam memória e tempo.
5. **Generators para streams grandes** — não materialize em lista se só vai
   iterar uma vez (`(x for x in ...)` em vez de `[x for x in ...]` quando não
   precisa indexar/reutilizar).

## Exemplo: cache de função pura

```python
from functools import lru_cache

@lru_cache(maxsize=256)
def calcula_preco_com_imposto(preco: float, aliquota: float) -> float:
    return preco * (1 + aliquota)
```

Só use `lru_cache` em funções verdadeiramente puras (mesma entrada -> mesma
saída, sem efeito colateral) — cachear uma função com estado externo (ex.: lê
banco de dados) pode devolver dado desatualizado.

## Sinal de alerta ao revisar código

- Loop que faz `if item in lista_grande:` repetidamente → sugerir `set`.
- Função pura chamada muitas vezes com os mesmos argumentos dentro de um loop
  → sugerir `lru_cache` ou calcular fora do loop.
- `requests`/chamada de rede síncrona dentro de função `async def` → bloqueia
  o event loop, precisa de cliente async ou `asyncio.to_thread`.
- `multiprocessing`/threads usados para acelerar cálculo puro de Python sem
  medir primeiro → confirmar que é CPU-bound antes de adicionar a complexidade.
