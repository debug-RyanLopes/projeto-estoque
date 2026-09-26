# pandas

## Vetorização em vez de loop linha a linha

```python
# Errado — itera linha a linha, lento para DataFrames grandes
for i, row in df.iterrows():
    df.at[i, "total"] = row["quantidade"] * row["preco"]

# Certo — operação vetorizada, ordens de magnitude mais rápida
df["total"] = df["quantidade"] * df["preco"]
```

`iterrows()`/`itertuples()` só se justificam quando a operação realmente não
tem equivalente vetorizado (lógica muito condicional linha a linha) — e mesmo
assim, `.apply()` costuma ser preferível a um loop `for` manual.

## `.apply()` tem seu próprio custo — prefira vetorizado quando existir

```python
# Aceitável quando não há operação vetorizada equivalente
df["categoria_normalizada"] = df["categoria"].apply(str.lower)

# Melhor quando existe o equivalente vetorizado nativo
df["categoria_normalizada"] = df["categoria"].str.lower()
```

`.str`, `.dt`, e operadores aritméticos diretos em Series são vetorizados em C —
`.apply()` roda uma função Python por linha, sempre mais lento.

## Filtragem: `.loc`/boolean indexing, não loop com `if`

```python
# Errado
resultado = []
for i, row in df.iterrows():
    if row["quantidade"] < 10:
        resultado.append(row)
baixo_estoque = pd.DataFrame(resultado)

# Certo
baixo_estoque = df.loc[df["quantidade"] < 10]

# Múltiplas condições: parênteses obrigatórios em cada condição
filtro = (df["quantidade"] < 10) & (df["categoria"] == "eletrônicos")
resultado = df.loc[filtro]
```

## `SettingWithCopyWarning`: entender antes de silenciar

```python
# Gera o warning — não está claro se `subset` é view ou cópia do df original
subset = df[df["categoria"] == "eletrônicos"]
subset["total"] = subset["quantidade"] * subset["preco"]  # pode não afetar df original

# Correto — copiar explicitamente quando a intenção é um DataFrame independente
subset = df[df["categoria"] == "eletrônicos"].copy()
subset["total"] = subset["quantidade"] * subset["preco"]
```

Nunca `.filterwarnings("ignore")` esse warning sem entender a causa — ele existe
porque o comportamento (view vs cópia) é ambíguo e pode silenciosamente não
alterar o DataFrame que você pensa que está alterando.

## `groupby` para agregações em vez de loop manual

```python
# Errado
totais = {}
for categoria in df["categoria"].unique():
    totais[categoria] = df[df["categoria"] == categoria]["quantidade"].sum()

# Certo
totais = df.groupby("categoria")["quantidade"].sum()
```

## Concatenar em loop: sempre acumular e concatenar uma vez só

```python
# Errado — O(n²), cada concat recopia tudo
resultado = pd.DataFrame()
for arquivo in arquivos:
    resultado = pd.concat([resultado, pd.read_csv(arquivo)])

# Certo — acumula em lista, concatena uma única vez no final
partes = [pd.read_csv(arquivo) for arquivo in arquivos]
resultado = pd.concat(partes, ignore_index=True)
```

## Tipos: `Int64`/`Float64` (nullable) quando há dados faltantes

```python
# int64 comum não aceita NaN — pandas converte a coluna inteira para float
df["quantidade"] = df["quantidade"].astype("Int64")  # nullable, aceita <NA>
```

## Checklist ao revisar código pandas

- [ ] Nenhum `iterrows()`/loop manual onde existe operação vetorizada equivalente.
- [ ] Filtragem usa boolean indexing/`.loc`, não loop com `if`.
- [ ] `.copy()` explícito quando a intenção é um DataFrame independente do original.
- [ ] Concatenação em loop acumula numa lista e chama `pd.concat` uma vez, não dentro do loop.
- [ ] Agregações por grupo usam `groupby`, não loop manual sobre valores únicos.
