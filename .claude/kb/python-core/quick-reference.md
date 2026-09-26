# Python Core — Quick Reference

Tabela de decisão para escolhas recorrentes. Se a resposta não estiver clara aqui,
ver o arquivo de `concepts/` correspondente.

## Estrutura de dados: qual usar?

| Preciso de... | Use | Não use |
|---|---|---|
| Registro imutável com campos nomeados, leve | `NamedTuple` ou `@dataclass(frozen=True)` | dict solto |
| Registro mutável com validação/métodos | `@dataclass` | dict solto, classe manual com `__init__` repetitivo |
| Conjunto fixo de valores nomeados (status, categoria) | `enum.Enum` / `enum.StrEnum` (3.11+) | strings mágicas soltas pelo código |
| Lookup por chave, tamanho variável | `dict` | lista + busca linear |
| Teste de pertencimento (`in`) frequente | `set` | `list` (busca é O(n) numa lista) |
| Interface que várias classes não-relacionadas implementam | `typing.Protocol` (duck typing estático) | herança forçada de uma base comum |
| Payload de API / dado externo com validação | Pydantic `BaseModel` (ver [frameworks/patterns/pydantic.md](../frameworks/patterns/pydantic.md)) | dict cru sem validação |

## Iteração e transformação

| Situação | Idioma |
|---|---|
| Transformar cada item de uma coleção | list/dict/set comprehension (se couber em 1 linha legível) |
| Coleção grande, só vai iterar uma vez | generator expression / função geradora (`yield`) — evita materializar tudo em memória |
| Precisa do índice e do valor | `enumerate(seq)`, nunca `range(len(seq))` |
| Percorrer duas listas em paralelo | `zip(a, b)` |
| Construir string a partir de partes | `"".join(partes)` — nunca `+=` em loop |
| Valor default em dict | `dict.get(k, default)` ou `collections.defaultdict` — nunca `if k in d: ... else: ...` manual |
| Contar ocorrências | `collections.Counter` |

## Concorrência: qual modelo?

| Cenário | Modelo |
|---|---|
| I/O-bound (rede, disco, muitas requisições) | `asyncio` (se a stack já é async) ou threads |
| CPU-bound (cálculo pesado) | `multiprocessing` ou `concurrent.futures.ProcessPoolExecutor` — threads não ajudam por causa do GIL |
| Poucas tarefas paralelas simples | `concurrent.futures.ThreadPoolExecutor` |
| Servidor web moderno | Framework async (FastAPI) se I/O-bound; framework sync (Flask/Django clássico) se CPU-bound ou simples |

## Erros comuns a sinalizar em revisão

- Argumento default mutável (`def f(x, cache=[])`) → usar `None` + criar dentro da função.
- `except Exception:` ou `except:` genérico escondendo o erro real.
- Arquivo/conexão aberto sem `with`.
- `==` para comparar `None`/singletons → usar `is None`.
- Comparação direta de float (`a == b`) → usar `math.isclose(a, b)`.
- String formatada com `%` ou `.format()` quando f-string resolveria mais claro.

Ver [concepts/idioms-and-style.md](concepts/idioms-and-style.md) e
[concepts/error-handling-and-resources.md](concepts/error-handling-and-resources.md) para
detalhes e exemplos de cada item acima.
