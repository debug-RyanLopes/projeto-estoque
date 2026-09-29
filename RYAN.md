# RYAN — Guia completo do feedback sobre o projeto de estoque

> Este arquivo é para **você**, Ryan. Ele explica, em linguagem simples, cada ponto que seu mentor levantou, **o que foi mudado no código** e **o que estudar** para dominar cada assunto. Não precisa ler tudo de uma vez — use como consulta.

## Índice

1. [Resumo em 1 minuto](#1-resumo-em-1-minuto)
2. [Recado importante sobre o feedback](#2-recado-importante-sobre-o-feedback)
3. [As 3 correções obrigatórias](#3-as-3-correções-obrigatórias)
   - [3.1 Testes mexendo no banco real](#31-testes-criandoatualizando-o-banco-real-estoquedb)
   - [3.2 Condição de corrida no cadastro (TOCTOU)](#32-condição-de-corrida-no-cadastro-toctou)
   - [3.3 Tailwind via CDN vs. README](#33-readme-diz-sem-serviços-externos-mas-o-tailwind-vem-de-cdn)
4. [As 5 melhorias sugeridas](#4-as-5-melhorias-sugeridas)
   - [4.1 `async def` chamando SQLAlchemy síncrono](#41-rotas-async-def-chamando-sqlalchemy-síncrono)
   - [4.2 Atualização atômica do saldo](#42-atualização-atômica-do-saldo-de-estoque)
   - [4.3 Camada de serviço](#43-camada-de-serviço)
   - [4.4 Configuração por ambiente + migrações](#44-configuração-por-ambiente--migrações)
   - [4.5 Histórico de movimentações imutável](#45-histórico-de-movimentações-como-registro-imutável)
5. [Mapa do projeto: o que mudou e onde](#5-mapa-do-projeto-o-que-mudou-e-onde)
6. [Como ver tudo funcionando](#6-como-ver-tudo-funcionando)
7. [O que ainda não está perfeito (honestidade)](#7-o-que-ainda-não-está-perfeito)
8. [Guia de estudos](#8-guia-de-estudos)
9. [Mini-glossário](#9-mini-glossário)

---

## 1. Resumo em 1 minuto

Seu mentor disse que a **arquitetura escolhida é adequada** (FastAPI + SQLAlchemy + SQLite + Jinja2 para um sistema de estoque local é uma boa escolha), e apontou:

| Tipo | Ponto | Em uma frase | Status |
|---|---|---|---|
| 🔴 Corrigir | Testes usam o `estoque.db` real | Rodar `pytest` podia criar/alterar seus dados de verdade | ✅ Corrigido |
| 🔴 Corrigir | Condição de corrida no cadastro | Dois cadastros ao mesmo tempo com o mesmo SKU podiam dar erro 500 | ✅ Corrigido |
| 🔴 Corrigir | README × CDN do Tailwind | README dizia "sem serviços externos", mas a página baixava CSS da internet | ✅ Corrigido |
| 🟡 Melhorar | `async def` + banco síncrono | A forma errada de misturar as duas coisas pode travar o servidor | ✅ Melhorado |
| 🟡 Melhorar | Saldo atômico | Duas saídas simultâneas podiam "vender o mesmo estoque duas vezes" | ✅ Melhorado |
| 🟡 Melhorar | Camada de serviço | Regras de negócio estavam misturadas com as rotas | ✅ Melhorado |
| 🟡 Melhorar | Config por ambiente + migrações | Banco fixo no código e tabelas criadas "no susto" | ✅ Melhorado |
| 🟡 Melhorar | Histórico imutável | Apagar um produto apagava também todo o histórico dele | ✅ Melhorado |

---

## 2. Recado importante sobre o feedback

Vários itens do feedback têm a ver com **concorrência**: "e se duas pessoas (ou duas abas do navegador, ou dois cliques rápidos) fizerem a mesma coisa *ao mesmo tempo*?"

No seu computador, testando sozinho, tudo funciona — porque você só faz **uma coisa de cada vez**. Bugs de concorrência só aparecem quando há duas coisas acontecendo juntas, e por isso são traiçoeiros: passam nos testes, passam quando você testa na mão, e quebram em produção uma vez a cada mil.

Um programador experiente aprende a se perguntar, para **todo** código que lê e depois escreve algo:

> **"O que acontece se outra requisição entrar entre a minha leitura e a minha escrita?"**

Se você guardar só uma coisa deste arquivo, guarde essa pergunta. Ela resolve os itens 3.2, 4.1 e 4.2.

---

## 3. As 3 correções obrigatórias

### 3.1 Testes criando/atualizando o banco real (`estoque.db`)

#### O que o mentor disse
> "Ao rodar a suíte de testes cria/atualiza o banco de dados real `estoque.db`, contradizendo o isolamento documentado."

#### Traduzindo
Seu README prometia: *"os testes nunca tocam no `estoque.db` real"*. Mas isso não era 100% verdade.

Analogia: você contrata um ator para **ensaiar** uma peça (o teste), e diz que ele vai usar um cenário de papelão (banco de teste). Mas, sem você perceber, na hora de "abrir o teatro" o ensaio também **montava o cenário real**. Ninguém quebrou nada, mas a promessa "só usamos o de papelão" era falsa.

#### Por que acontecia (a causa técnica)
No `app/main.py` antigo, havia isto:

```python
@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(bind=engine)   # <- engine = banco REAL
    yield
```

O `TestClient(app)` dispara o `lifespan` quando "liga" a aplicação. Então, a cada teste, o `create_all` rodava no **engine global**, que apontava para `sqlite:///./estoque.db`. Se o arquivo não existisse, ele era **criado**. O `dependency_overrides` do `conftest.py` só trocava o banco usado **dentro das rotas** (`get_db`) — mas não o do `lifespan`.

> Note que isso não apagava seus dados. Mas *criava/tocava* o arquivo real, e isso basta para quebrar a promessa de isolamento. Em um sistema maior, poderia ter sido pior.

#### O que foi feito
1. **Removi o `create_all` da aplicação.** Quem cria as tabelas agora são as *migrações* (ver 4.4). A aplicação deixou de ter "efeito colateral ao ligar".
2. **`tests/conftest.py` blinda os testes ANTES de importar a aplicação:**
   ```python
   os.environ["APP_ENV"] = "test"
   os.environ["DATABASE_URL"] = "sqlite:///" + <pasta temporária> + "/global.db"
   # só depois: from app.main import app
   ```
   Assim, mesmo que alguma rota/engine global seja usada por engano, ela aponta para uma pasta temporária.
3. Cada teste ainda recebe seu **próprio banco** em arquivo temporário (fixture `session_factory`).
4. **Novo teste** `test_suite_nunca_aponta_para_o_banco_real` garante que o banco da suíte nunca é `estoque.db`.
5. Eu também **provei na prática**: copiei o projeto para uma pasta sem `estoque.db`, rodei os 14 testes, e nenhum `.db` foi criado lá.

#### O que estudar
- pytest **fixtures** e `conftest.py`
- `monkeypatch` e variáveis de ambiente em testes
- Conceito de **isolamento de testes** e **efeito colateral**

---

### 3.2 Condição de corrida no cadastro (TOCTOU)

#### O que o mentor disse
> "Cadastro de produto tem condição de corrida (TOCTOU) sem tratamento de erro de banco."

#### Traduzindo
**TOCTOU** = *Time Of Check To Time Of Use* = "Tempo entre **checar** e **usar**".

Analogia do banheiro público: você olha pela fresta e vê que a cabine está **livre** (checou). Enquanto você dá dois passos até a porta, outra pessoa entra (algo mudou). Você abre a porta e... ocupado (usou com base numa informação velha).

#### O código antigo
```python
if db.query(Produto).filter(Produto.sku == sku).first():   # 1. CHECA: "esse SKU existe?"
    return _redirect_com_erro("SKU já cadastrado")

produto = Produto(sku=sku, ...)                            # 2. USA: insere
db.add(produto)
db.commit()
```

Linha do tempo com **dois cadastros simultâneos** do SKU `PAR-M6`:

| Momento | Requisição A | Requisição B |
|---|---|---|
| 1 | Checa: "PAR-M6 existe?" → **não** | |
| 2 | | Checa: "PAR-M6 existe?" → **não** (A ainda não gravou!) |
| 3 | Insere e faz commit ✅ | |
| 4 | | Insere... 💥 o banco recusa (coluna `sku` é `unique=True`) |

Como não havia tratamento, o erro do banco (`IntegrityError`) subia como **erro 500** — uma tela quebrada para o usuário.

Ou seja, o `if` **nunca conseguiria garantir** a unicidade. Quem garante é o **banco de dados** (a constraint `UNIQUE`). O `if` era só uma gentileza, e mesmo assim tinha um buraco.

#### A regra de ouro
> **Não pergunte "posso?" e depois faça. Faça, e trate o "não".**

Em inglês, isso é o princípio *"EAFP — Easier to Ask Forgiveness than Permission"* (mais fácil pedir perdão do que permissão), muito usado em Python.

#### O que foi feito (`app/services.py`)
```python
db.add(produto)
try:
    db.commit()
except IntegrityError as exc:
    db.rollback()
    raise SkuDuplicadoError(sku) from exc
```
- Removi o "SELECT antes". Insere direto.
- Se o banco recusar por SKU repetido, desfazemos (`rollback`) e viramos isso em um erro **de negócio** com mensagem amigável ("SKU 'X' já cadastrado"), que a rota transforma no aviso vermelho da tela. Nunca mais 500.
- O `rollback()` é importante: depois de um erro, a sessão fica "suja", e sem ele a sessão ficaria inutilizável.

#### Como testamos
`test_cadastro_simultaneo_do_mesmo_sku_gera_um_unico_produto` dispara **8 threads ao mesmo tempo** cadastrando o mesmo SKU. Resultado esperado (e obtido): **1 sucesso, 7 erros de negócio, 0 erros crus**, e só 1 produto no banco.

#### O que estudar
- **Race condition / TOCTOU**
- **Constraints do banco** (`UNIQUE`, `NOT NULL`, `FOREIGN KEY`) — o banco é a última linha de defesa
- Tratamento de exceção no SQLAlchemy: `IntegrityError`, `rollback()`
- Princípio **EAFP** vs **LBYL** ("Look Before You Leap") em Python

---

### 3.3 README diz "sem serviços externos", mas o Tailwind vem de CDN

#### O que o mentor disse
> "README afirma que o sistema não depende de serviços externos, mas o template carrega Tailwind via CDN público (a troca do CDN pelo CSS local)."

#### Traduzindo
O README dizia: *"Roda inteiramente na sua máquina, sem depender de serviços externos"*.
Mas o `base.html` tinha:

```html
<script src="https://cdn.tailwindcss.com"></script>
```

Ou seja, **toda vez** que você abria a página, o navegador baixava o Tailwind da internet. Sem internet → página **sem estilo nenhum**. O sistema dependia, sim, de um serviço externo. A documentação e o código se contradiziam.

Além disso, o próprio Tailwind avisa que o script do CDN é **só para desenvolvimento/protótipo**: ele roda um compilador *dentro do navegador* a cada carregamento (lento) e baixa bem mais do que precisa.

#### Como o Tailwind funciona (importante entender!)
O Tailwind é um *gerador de CSS*. Você escreve classes no HTML (`bg-moss-dark`, `px-4`...). Alguém precisa ler seus templates e **gerar um arquivo `.css`** contendo só as regras que você usou.
- **Modo CDN**: esse "alguém" é o navegador, toda vez. (Prático, mas dependente da internet.)
- **Modo build**: esse "alguém" é uma ferramenta (o *Tailwind CLI*) que você roda **uma vez** e gera um `.css` estático. O navegador só baixa o arquivo do **seu** servidor.

#### O que foi feito
1. `tailwind.config.js` (na raiz) — guarda o tema/cores (`moss`, etc.) que antes ficavam dentro do `<script>` do HTML.
2. `app/static/css/input.css` — as 3 linhas de entrada do Tailwind.
3. `app/static/css/tailwind.css` — **o CSS gerado** (~11 KB, contra centenas de KB do CDN). Está commitado no repositório, então **você não precisa de Node.js para rodar o projeto**, só para *regenerar* o CSS.
4. `base.html` agora usa `<link rel="stylesheet" href="{{ url_for('static', path='css/tailwind.css') }}">`.
5. `app/main.py` monta a pasta `/static` com `StaticFiles`.
6. `make css` regenera o arquivo quando você mudar classes nos templates.
7. README e CLAUDE.md atualizados.
8. Teste `test_pagina_usa_css_local_e_nao_cdn` falha se algum `src`/`href` apontar para fora do servidor. (Conferi: com o `base.html` antigo esse teste falha.)

> ⚠️ **Atenção futura:** se você adicionar uma classe nova num template (ex.: `bg-blue-500`) e não rodar `make css`, ela **não vai funcionar**, porque o CSS gerado não a conhece. Esse é o "preço" do modo build.

#### O que estudar
- Tailwind: **modo CDN vs build (CLI)**, arquivo `tailwind.config.js`, opção `content`
- FastAPI: **arquivos estáticos** (`StaticFiles`) e `url_for`
- Ideia de **"funciona offline"** e de **consistência entre documentação e código**

---

## 4. As 5 melhorias sugeridas

### 4.1 Rotas `async def` chamando SQLAlchemy síncrono

#### O que o mentor disse
> "As Rotas `async def` chamando SQLAlchemy síncrono"

#### Traduzindo — a analogia do restaurante
Imagine um restaurante com **um garçom só** (o *event loop* do `async`). O garçom é ótimo porque, quando um pedido está na cozinha, ele já atende outra mesa (isso é *concorrência assíncrona*: "enquanto espero, faço outra coisa").

Mas isso só funciona se o garçom **avisa** quando vai esperar (`await`). Um `db.query(...)` síncrono **não avisa**: ele fica parado na frente da cozinha, de braços cruzados, esperando o prato. **Todas as outras mesas ficam sem atendimento** enquanto isso.

Ou seja: com `async def` + banco síncrono, você tem a **pior combinação**: parece assíncrono, mas cada consulta ao banco **trava o servidor inteiro**.

#### O que o FastAPI faz de diferente
- `async def rota()` → roda **direto no event loop** (o garçom único). Só use se tudo dentro for `await`.
- `def rota()` → o FastAPI roda em um **pool de threads** (vários "ajudantes"), sem travar o garçom. **É o certo para código bloqueante** (SQLAlchemy síncrono, `requests`, leitura de arquivo etc.)

#### O que foi feito
Troquei todas as rotas de `async def` para `def` em `app/main.py`, com um comentário explicando o porquê. Na prática, **o código ficou até mais simples** (nenhuma linha muda além do `async`).

> Existe uma alternativa: usar **SQLAlchemy assíncrono** (`AsyncSession` + driver `aiosqlite`) e aí sim `async def` + `await`. Para um sistema local de uma pessoa, seria complexidade sem ganho. A escolha certa é a **mais simples que funciona**: `def`.

#### O que estudar
- Diferença entre **concorrência, paralelismo, threads e event loop**
- `async`/`await` em Python (módulo `asyncio`)
- Documentação do FastAPI: *"Concurrency and async / await"* — tem exatamente essa analogia do restaurante (hambúrguer)
- **I/O bound** vs **CPU bound**

---

### 4.2 Atualização atômica do saldo de estoque

#### O que o mentor disse
> "Atualização atômica do saldo de estoque"

#### Traduzindo
**Atômico** = "indivisível": acontece **inteiro ou não acontece**, e ninguém consegue enxergar o "meio" da operação.

#### O código antigo e o bug (*lost update*)
```python
produto = db.get(Produto, produto_id)             # 1. LÊ o saldo (ex.: 10)
if quantidade > produto.quantidade: ...           # 2. CONFERE (5 > 10? não, ok)
produto.quantidade += -quantidade                 # 3. Calcula no Python (10 - 5 = 5)
db.commit()                                       # 4. GRAVA 5
```

Cenário: saldo = **10**. Duas pessoas registram **saída de 8** ao mesmo tempo.

| Momento | Pessoa A | Pessoa B |
|---|---|---|
| 1 | Lê saldo: 10 | |
| 2 | | Lê saldo: 10 |
| 3 | 8 ≤ 10 ✅ → calcula 10−8 = 2 | |
| 4 | | 8 ≤ 10 ✅ → calcula 10−8 = 2 |
| 5 | Grava 2 | |
| 6 | | Grava 2 |

Resultado: **saíram 16 unidades de um estoque de 10**, e o sistema diz que sobraram 2. Você "vendeu" o que não tinha. Esse bug se chama **lost update** (atualização perdida). É o mesmo problema do TOCTOU (item 3.2): **ler → decidir → gravar** com um buraco no meio.

#### A solução: deixar o BANCO fazer a conta, numa instrução só
```python
stmt = (
    update(Produto)
    .where(Produto.id == produto_id, Produto.ativo.is_(True))
    .values(quantidade=Produto.quantidade + delta)   # o banco calcula: quantidade = quantidade + delta
)
if tipo == "saida":
    stmt = stmt.where(Produto.quantidade >= quantidade)   # só atualiza SE tiver saldo
```
Em SQL puro:
```sql
UPDATE produtos SET quantidade = quantidade - 8 WHERE id = 1 AND quantidade >= 8;
```

Por que funciona: o banco **executa cada UPDATE de forma indivisível**, uma de cada vez. A conta e a verificação (`quantidade >= 8`) acontecem no mesmo passo. Refazendo o cenário:
- A executa primeiro: saldo 10 ≥ 8 ✅ → vira 2. (1 linha afetada)
- B executa depois: saldo agora é 2, `2 >= 8` é falso → **0 linhas afetadas**.

Então o código olha `rowcount`: se for **0**, ninguém foi atualizado → ou o produto não existe, ou faltou saldo → erro amigável "Estoque insuficiente". O saldo **nunca fica negativo**, mesmo com 100 pessoas ao mesmo tempo.

Além disso, o UPDATE do saldo e o INSERT da movimentação acontecem **na mesma transação**: ou os dois valem, ou nenhum.

#### Como testamos
`test_saidas_simultaneas_nunca_deixam_estoque_negativo`: estoque 10, **8 threads** tentam sair 5 unidades cada. Só **2** podem vencer (2×5 = 10). O teste verifica: 6 erros de "estoque insuficiente", saldo final **0**, exatamente **2** saídas registradas.

#### O que estudar
- **Transações** e propriedades **ACID** (Atomicidade, Consistência, Isolamento, Durabilidade)
- **Lost update**, **read-modify-write**
- **Níveis de isolamento** de transação
- **Bloqueio otimista vs pessimista** (`SELECT ... FOR UPDATE`, coluna `version`)
- SQLAlchemy 2.0: `update()` com expressões (`Produto.quantidade + delta`) e `result.rowcount`

---

### 4.3 Camada de serviço

#### O que o mentor disse
> "Camada de serviço separando regra de negócio das rotas"

#### Traduzindo — a analogia do restaurante (de novo)
- A **rota** é o **garçom**: recebe o pedido do cliente (HTTP), leva para a cozinha e entrega o prato de volta (redirect/HTML). Ele não cozinha.
- O **serviço** é a **cozinha**: sabe as receitas (regras de negócio): "não pode sair mais do que tem", "SKU é único".
- O **modelo/banco** é a **despensa**.

Antes, o garçom cozinhava: as regras estavam **dentro** das funções de rota, misturadas com detalhes de HTTP (`Form`, `RedirectResponse`, `quote`, `HTTPException`).

#### Por que separar?
1. **Testabilidade**: dá para testar a regra "saída maior que o estoque" **sem** simular requisição HTTP. (`tests/test_servicos.py` chama funções normais.)
2. **Reuso**: amanhã você cria uma API JSON, um comando de terminal ou uma importação de planilha — todos chamam o **mesmo** serviço, sem copiar regra.
3. **Legibilidade**: cada arquivo tem uma responsabilidade.
4. **Onde mora a concorrência**: as decisões de 3.2 e 4.2 ficam num lugar só.

#### Como ficou
```
Navegador ──HTTP──▶ app/main.py (rotas)  ──chama──▶ app/services.py (regras) ──usa──▶ app/models.py ──▶ banco
                     "traduz HTTP"                    "decide e valida"
```

Rota (antes, ~15 linhas de lógica; agora só traduz):
```python
@app.post("/movimentacoes")
def registrar_movimentacao(produto_id, tipo, quantidade, db):
    try:
        services.registrar_movimentacao(db, produto_id, tipo, quantidade)
    except services.ProdutoNaoEncontradoError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except services.EstoqueError as exc:
        return _redirect_com_erro(str(exc))
    return RedirectResponse(url="/", status_code=303)
```

**Exceções de negócio** (`EstoqueError` e filhas: `SkuDuplicadoError`, `EstoqueInsuficienteError`, ...): o serviço **não sabe o que é HTTP**. Ele só diz "isso deu errado, por este motivo". Quem decide *como mostrar* (redirect com erro, 404, JSON...) é a rota.

> Regra prática: **se você precisar importar `fastapi` dentro de `services.py`, algo está no lugar errado.** (Confira: o arquivo não importa nada de FastAPI.)

#### O que estudar
- **Arquitetura em camadas** (apresentação / negócio / dados)
- **Separação de responsabilidades** e **Single Responsibility Principle** (o "S" do SOLID)
- Padrões **Service Layer** e **Repository** (o Repository você ainda não precisa)
- Livro gratuito online *"Architecture Patterns with Python"* (cosmicpython.com) — os primeiros capítulos tratam exatamente disso
- **Exceções customizadas** em Python

---

### 4.4 Configuração por ambiente + migrações

Esses são **dois assuntos** juntos.

#### (a) Configuração por ambiente

##### O que o mentor disse
> "Configuração por ambiente"

##### Traduzindo
Antes, o banco estava **fixo no código**: `DATABASE_URL = "sqlite:///./estoque.db"`. Para usar outro banco (testes, produção, seu amigo), você teria que **editar o código**. Isso é ruim porque:
- Você pode commitar por engano uma configuração de outro ambiente.
- Não dá para ter valores diferentes (dev/teste/produção) sem mexer em arquivos.
- Segredos (senhas de banco, chaves de API) **nunca** devem ficar no código.

O princípio (*The Twelve-Factor App*, fator "Config"): **configuração vem do ambiente, o código é o mesmo em todo lugar.**

##### O que foi feito (`app/config.py`)
```python
APP_ENV       = dev (padrão) | test | prod
DATABASE_URL  = sobrescreve o banco (opcional)
```
- Sem configurar nada, tudo funciona igual (`estoque.db`).
- Com `DATABASE_URL=sqlite:///outro.db`, o mesmo código usa outro banco.
- `APP_ENV=test` usa um banco de teste por padrão (é isso que blinda os testes, ver 3.1).
- Um `APP_ENV` inválido causa erro **na hora** com mensagem clara (*fail fast*: falhar cedo e alto é melhor que falhar tarde e em silêncio).

Como usar no PowerShell:
```powershell
$env:DATABASE_URL = "sqlite:///./meu_outro_banco.db"
uvicorn app.main:app
```

#### (b) Migrações

##### O que o mentor disse
> "...+ migrações"

##### Traduzindo
Um banco de dados tem um **schema** (as tabelas e colunas). Seu código muda com o tempo: hoje você quer adicionar a coluna `ativo`. Como levar essa mudança para o **banco que já existe e já tem dados**?

Antes você usava `create_all`, que só **cria tabelas que não existem**. Se a tabela `produtos` já existe, ele **não adiciona coluna nenhuma**. Sua única saída seria apagar o banco (e perder os dados) ou editar tudo à mão.

**Migração** = um "commit para o banco de dados". É um pequeno script versionado que diz *"como ir da versão N para a N+1 do schema"*. Assim:
- O schema tem **histórico**, como o código no Git.
- Qualquer pessoa/máquina chega ao **mesmo schema** rodando `alembic upgrade head`.
- Dá para **voltar atrás** (`downgrade`).
- Os **dados existentes são preservados**.

##### O que foi feito (Alembic)
- `alembic.ini` + pasta `migrations/`
- `migrations/env.py` — usa a mesma URL de banco e os mesmos modelos da aplicação
- `migrations/versions/0001_baseline.py` — cria `produtos` e `movimentacoes` (**se já existirem**, por causa do seu `estoque.db` antigo, apenas não recria)
- `migrations/versions/0002_produto_ativo.py` — adiciona a coluna `ativo` (usada no item 4.5)
- `make migrate` e `make run` (que migra antes de subir o servidor)
- Teste `test_migracoes_produzem_o_mesmo_schema_dos_modelos`: aplica as migrações num banco novo e compara com os modelos do Python. Se você alterar `models.py` e esquecer de gerar migração, **esse teste falha**.

Testei a migração num banco "antigo" (sem a coluna `ativo`, com um produto dentro): ele foi migrado e **o produto e a quantidade continuaram lá**.

Fluxo do dia a dia quando mudar um modelo:
```powershell
# 1. edite app/models.py
alembic revision --autogenerate -m "adiciona coluna X"   # 2. gera o script
# 3. LEIA o script gerado (o autogenerate erra às vezes!)
alembic upgrade head                                      # 4. aplica
```

> ⚠️ **Seu `estoque.db` atual** ainda não tem a coluna `ativo`. Na primeira vez que você rodar `make run` (ou `alembic upgrade head`), ela é adicionada automaticamente, **sem perder dados**. Se preferir ser cauteloso, copie o arquivo `estoque.db` antes.

> 💡 **SQLite e `ALTER TABLE`**: o SQLite não sabe fazer vários tipos de alteração de tabela. O Alembic contorna com o modo *batch* (`render_as_batch=True`): cria uma tabela nova, copia os dados e troca. É por isso que você vê `batch_alter_table` na migração 0002.

#### O que estudar
- **Twelve-Factor App** — fator III (Config): 12factor.net/pt_br
- Variáveis de ambiente, `os.environ`, arquivos `.env` (e por que **não** commitá-los)
- **Alembic**: tutorial oficial (`alembic init`, `revision --autogenerate`, `upgrade`, `downgrade`, `stamp`)
- Conceitos: **schema**, **versionamento de banco**, **migração para frente/para trás**, **fail fast**
- Bônus: **pydantic-settings** (biblioteca que valida configuração; é o próximo passo natural do `config.py`)

---

### 4.5 Histórico de movimentações como registro imutável

#### O que o mentor disse
> "Histórico de movimentações como registro imutável"

#### Traduzindo — a analogia do extrato bancário
O seu banco **nunca apaga** uma linha do extrato. Se você fez uma transferência errada, o banco não "edita" o passado: cria um **novo lançamento de estorno**. É isso que se chama de registro **imutável** (*append-only*: só se acrescenta no fim).

Por que isso importa para estoque?
- **Auditoria**: "por que o saldo está assim?" → o histórico tem a resposta.
- **Confiança**: se dá para editar/apagar o passado, ninguém confia nos números.
- **Depuração**: você consegue reconstruir o saldo somando as movimentações.

#### O problema no código antigo
Duas coisas quebravam isso:
1. `cascade="all, delete-orphan"` no relacionamento: **apagar um produto apagava todo o histórico dele** (o extrato inteiro sumia).
2. Nada impedia que uma movimentação fosse alterada ou apagada em outro pedaço do código.

#### O que foi feito
1. **Exclusão lógica (*soft delete*)**: adicionei a coluna `Produto.ativo`. "Excluir" agora só muda `ativo` para `False`: o produto **some da tela**, mas o registro e o **histórico permanecem**. (Removido o `cascade` de exclusão.)
2. **`Movimentacao` protegida**: um *event listener* do SQLAlchemy bloqueia qualquer `UPDATE` ou `DELETE` de uma movimentação, lançando `MovimentacaoImutavelError`:
   ```python
   @event.listens_for(Movimentacao, "before_update")
   @event.listens_for(Movimentacao, "before_delete")
   def _bloquear_alteracao_de_movimentacao(mapper, connection, target):
       raise MovimentacaoImutavelError(...)
   ```
   Se um dia você precisar corrigir um erro, a regra é: **registre uma nova movimentação de ajuste**, não edite a antiga.
3. **Chaves estrangeiras ligadas no SQLite** (`PRAGMA foreign_keys=ON`): o SQLite, por padrão, *ignora* `FOREIGN KEY`! Sem isso, o banco aceitaria movimentação apontando para produto inexistente.
4. `data` agora usa horário UTC **com fuso** (o `datetime.utcnow()` antigo está *deprecated* no Python 3.12+).

Testes: `test_movimentacao_nao_pode_ser_alterada_nem_apagada` e `test_excluir_produto_preserva_historico`.

> **Consequência a conhecer:** como o produto "excluído" continua na tabela, o **SKU dele continua ocupado**. Cadastrar outro produto com o mesmo SKU dá "SKU já cadastrado". É uma decisão de negócio possível de mudar depois (ex.: botão "reativar produto").

> **Limite da proteção atual:** ela vale para quem usa o SQLAlchemy da aplicação. Alguém com acesso direto ao arquivo `.db` ainda poderia editar por SQL. A proteção "de verdade" seria um *trigger* no próprio banco (ver seção 7).

#### O que estudar
- **Soft delete** vs **hard delete**
- **Append-only log**, **Event Sourcing** (só o conceito, é um tema avançado), **Ledger** (livro-razão)
- **Trilha de auditoria** (*audit trail*)
- SQLAlchemy: **eventos ORM** (`before_update`, `before_delete`) e `relationship(cascade=...)`
- **Integridade referencial** e `FOREIGN KEY` (e o `PRAGMA foreign_keys` do SQLite)

---

## 5. Mapa do projeto: o que mudou e onde

```
projeto-estoque/
├── RYAN.md                        ← este guia (novo)
├── alembic.ini                    ← config do Alembic (novo)
├── tailwind.config.js             ← tema/cores do Tailwind (novo)
├── Makefile                       ← + make migrate, + make css, run agora migra antes
├── requirements.txt               ← + alembic
├── README.md / CLAUDE.md          ← atualizados
├── app/
│   ├── config.py                  ← configuração por ambiente (novo)
│   ├── database.py                ← usa config; liga FOREIGN KEY no SQLite
│   ├── models.py                  ← + Produto.ativo; Movimentacao imutável; sem cascade de delete
│   ├── services.py                ← regras de negócio + decisões de concorrência (novo)
│   ├── main.py                    ← só rotas, agora `def`; monta /static; sem create_all
│   ├── static/css/                ← tailwind.css gerado + input.css (novo)
│   └── templates/base.html        ← CSS local em vez de CDN
├── migrations/                    ← Alembic: env.py + 0001_baseline + 0002_produto_ativo (novo)
└── tests/
    ├── conftest.py                ← isolamento forte (reescrito)
    ├── test_produtos.py           ← inalterado, continua passando
    ├── test_movimentacoes.py      ← inalterado, continua passando
    ├── test_servicos.py           ← concorrência, imutabilidade, soft delete (novo)
    └── test_infra.py              ← isolamento, migrações, sem CDN (novo)
```

Resultado dos testes: **14 passaram** (eram 5).

O `main.py` da **raiz** (script que usava a API paga da Anthropic) foi **removido**, junto com a dependência `anthropic`: o projeto não usa mais nenhuma chave de API nem serviço pago.

---

## 6. Como ver tudo funcionando

```powershell
# 1. Instalar a dependência nova (alembic)
pip install -r requirements.txt

# 2. Criar/atualizar o banco e subir o servidor
make run                      # ou: alembic upgrade head ; uvicorn app.main:app --reload

# 3. Rodar os testes
make test                     # ou: pytest
```

> Não tem `make` no Windows? Rode os comandos "ou:" ao lado (funcionam direto). O `make` só é um atalho.

Coisas legais para você **experimentar** e entender:

1. **Veja a proteção de estoque negativo**: cadastre um produto, dê entrada de 3 e tente saída de 100 → aviso vermelho.
2. **Veja o histórico sobreviver**: registre movimentações, exclua o produto e abra o banco:
   ```powershell
   python -c "import sqlite3; print(sqlite3.connect('estoque.db').execute('select * from movimentacoes').fetchall())"
   ```
3. **Veja o site funcionar sem internet**: desligue o Wi-Fi e recarregue a página. Antes: sem estilo. Agora: normal.
4. **Quebre de propósito** para entender o teste: em `services.py`, troque o `UPDATE` atômico pela versão antiga (ler → somar → gravar) e rode `pytest tests/test_servicos.py`. O teste de concorrência deve falhar (às vezes é preciso rodar algumas vezes; bugs de corrida são assim mesmo!).

---

## 7. O que ainda não está perfeito

Sendo honesto (e isso é uma habilidade de programador!): aqui vão limites que **eu não mexi** por não fazerem parte do feedback, mas que você deve conhecer e que seu mentor pode perguntar depois.

1. **Dinheiro em `float`**: `preco_compra` / `preco_venda` são `float` no Python. Números decimais em `float` têm imprecisão (`0.1 + 0.2 == 0.30000000000000004`). O correto para dinheiro é `Decimal` (ou guardar centavos como inteiro). O banco já usa `Numeric(10, 2)`; falta ajustar o Python.
2. **Sem autenticação**: qualquer pessoa que acesse a URL mexe no estoque. Ok para uso local pessoal; um problema se publicar na internet.
3. **Sem proteção CSRF** nos formulários (relacionado ao item anterior).
4. **Imutabilidade só no ORM**: um *trigger* no SQLite (`BEFORE UPDATE/DELETE ON movimentacoes ... RAISE(ABORT)`) daria proteção no nível do banco.
5. **SQLite e concorrência real**: SQLite serializa escritas (um escritor por vez). Ótimo para uso local; para muitos usuários simultâneos você migraria para PostgreSQL — e graças à configuração por ambiente (4.4) e ao Alembic, essa troca ficou muito mais fácil.
6. **Sem paginação**: a listagem carrega todos os produtos.
7. **Sem "reativar produto"** nem tela de histórico de movimentações: o dado existe, mas ainda não há interface para vê-lo.
8. **Sem linter/formatador** (`ruff`, `black`) nem tipagem estática (`mypy`).
9. **Rodei os comandos do Makefile manualmente, mas não o `make` em si**, pois não há `make` instalado no ambiente onde fiz as mudanças. Os alvos apenas repetem comandos que eu testei um a um.

Boas ideias para seu **próximo passo de estudo prático** (em ordem de dificuldade): (1) trocar `float` por `Decimal`; (2) criar uma tela de histórico de movimentações; (3) adicionar `ruff` e rodar no `make lint`; (4) criar um trigger no SQLite; (5) trocar SQLite por PostgreSQL usando Docker.

---

## 8. Guia de estudos

**Como usar:** siga a ordem. Cada bloco tem *o que aprender*, *termos para pesquisar* e *um exercício prático no seu próprio projeto*. Não precisa decorar; precisa **conseguir explicar com suas palavras** (o teste do "explique para um amigo").

Referências principais (todas gratuitas e oficiais):
- FastAPI: fastapi.tiangolo.com (a documentação é excelente e tem tradução em português)
- SQLAlchemy 2.0: docs.sqlalchemy.org → *"SQLAlchemy Unified Tutorial"*
- Alembic: alembic.sqlalchemy.org → *Tutorial*
- pytest: docs.pytest.org
- Tailwind: tailwindcss.com/docs
- SQLite: sqlite.org (páginas *"Isolation In SQLite"* e *"Transactions"*)
- Livro online: *Architecture Patterns with Python* — cosmicpython.com
- Livro: *Designing Data-Intensive Applications* (Martin Kleppmann) — o capítulo de **Transações** é a melhor explicação de concorrência em bancos que existe (avançado; leia depois do resto)

### Nível 1 — Fundamentos (faça primeiro)

**A) Banco de dados e SQL**
- **Aprender:** `SELECT`, `INSERT`, `UPDATE`, `DELETE`, `WHERE`, `JOIN`, chave primária, chave estrangeira, índice, constraint `UNIQUE`.
- **Pesquisar:** "SQL basics", "primary key vs foreign key", "unique constraint".
- **Exercício:** abra `estoque.db` num visualizador (DB Browser for SQLite, ou a extensão *SQLite Viewer* do VS Code) e escreva à mão o SQL para: listar produtos com estoque baixo; somar as entradas de um produto; achar produtos sem movimentações.

**B) Como a web funciona (HTTP)**
- **Aprender:** requisição/resposta, métodos `GET` e `POST`, códigos de status (`200`, `303`, `404`, `500`), formulários, redirecionamento.
- **Pesquisar:** "HTTP status codes", "Post/Redirect/Get pattern" (é o que seu app faz com o `303`).
- **Exercício:** abra o DevTools do navegador (F12 → aba *Network*), cadastre um produto e observe a requisição `POST /produtos` seguida do redirecionamento.

### Nível 2 — As ferramentas do projeto

**C) FastAPI e o modelo async**
- **Aprender:** rotas, `Depends` (injeção de dependência), `Form`, `StaticFiles`, `def` vs `async def`.
- **Pesquisar:** "FastAPI concurrency and async await", "event loop", "thread pool", "I/O bound vs CPU bound".
- **Relaciona com:** 4.1 e 4.3.
- **Exercício:** crie uma rota `GET /demo/lenta` com `def` que faz `time.sleep(5)` e outra com `async def` que também faz `time.sleep(5)`. Abra a página `/` em outra aba durante a espera. Perceba qual das duas **trava o site inteiro**.

**D) SQLAlchemy 2.0**
- **Aprender:** `Session`, modelos com `Mapped`/`mapped_column`, `select()`, `update()`, `relationship`, ciclo de vida (`add` → `commit` → `rollback`), `IntegrityError`.
- **Pesquisar:** "SQLAlchemy 2.0 unified tutorial", "SQLAlchemy session commit rollback", "identity map".
- **Relaciona com:** 3.2, 4.2 e 4.5.
- **Exercício:** no `services.py`, escreva uma função `historico_do_produto(db, produto_id)` que devolve as movimentações ordenadas por data.

**E) pytest**
- **Aprender:** funções `test_*`, `assert`, **fixtures**, `conftest.py`, `tmp_path`, `monkeypatch`, `parametrize`.
- **Pesquisar:** "pytest fixtures", "pytest conftest", "test isolation", "FastAPI TestClient", "dependency_overrides".
- **Relaciona com:** 3.1.
- **Exercício:** use `@pytest.mark.parametrize` para reduzir os 3 testes de cadastro repetidos em `test_produtos.py` (vários dicts iguais).

### Nível 3 — Os conceitos por trás do feedback (o mais importante!)

**F) Concorrência e condições de corrida**
- **Aprender:** o que é uma *race condition*; TOCTOU; *lost update*; por que "checar e depois agir" é perigoso; EAFP vs LBYL.
- **Pesquisar:** "race condition explained", "TOCTOU", "lost update problem", "read-modify-write", "EAFP vs LBYL Python".
- **Relaciona com:** 3.2 e 4.2.
- **Exercício:** leia `tests/test_servicos.py` (funções `_rodar_em_paralelo` e os 2 testes de concorrência) e explique em voz alta o papel do `threading.Barrier`. Depois execute a versão "quebrada" do experimento 4 da seção 6.

**G) Transações e ACID**
- **Aprender:** o que é uma transação; `BEGIN/COMMIT/ROLLBACK`; A.C.I.D.; níveis de isolamento; bloqueio otimista vs pessimista.
- **Pesquisar:** "database transactions ACID", "isolation levels", "SELECT FOR UPDATE", "optimistic locking version column", "SQLite isolation".
- **Relaciona com:** 4.2.
- **Exercício:** escreva, à mão, no SQL: `BEGIN; UPDATE ... ; ROLLBACK;` e observe que nada mudou. Depois com `COMMIT`.

**H) Arquitetura em camadas / regras de negócio**
- **Aprender:** separação de responsabilidades; service layer; por que a regra de negócio não deve saber de HTTP; exceções de domínio.
- **Pesquisar:** "layered architecture", "service layer pattern", "separation of concerns", "SOLID single responsibility", "domain exceptions".
- **Relaciona com:** 4.3.
- **Exercício:** adicione uma regra nova **só** em `services.py` (ex.: "estoque mínimo não pode ser maior que 10.000") e escreva o teste **sem** usar HTTP. Depois só ligue na rota.

**I) Configuração e migrações**
- **Aprender:** Twelve-Factor App (fator Config), variáveis de ambiente, Alembic (`revision --autogenerate`, `upgrade`, `downgrade`, `stamp`, `history`).
- **Pesquisar:** "twelve factor app config", "alembic tutorial", "alembic autogenerate limitations", "alembic sqlite batch mode".
- **Relaciona com:** 4.4.
- **Exercício:** adicione a coluna `localizacao` (texto opcional, ex.: "Prateleira A2") em `Produto`, gere a migração com `--autogenerate`, **leia o script** e aplique. Depois faça `alembic downgrade -1` e `alembic upgrade head` para ver ida e volta.

**J) Integridade de dados e histórico**
- **Aprender:** constraints como última defesa; soft delete; registros append-only; trilha de auditoria; integridade referencial.
- **Pesquisar:** "soft delete vs hard delete", "append only table", "audit log design", "foreign key constraint", "event sourcing basics".
- **Relaciona com:** 3.2 e 4.5.
- **Exercício:** crie uma tela `/historico` que lista as movimentações (data, produto, tipo, quantidade) — assim o "histórico imutável" fica visível para o usuário.

### Nível 4 — Front-end e entrega

**K) Tailwind e assets estáticos**
- **Aprender:** utilitários do Tailwind; CDN vs build; `content` no `tailwind.config.js`; arquivos estáticos; cache do navegador.
- **Pesquisar:** "Tailwind CLI", "Tailwind Play CDN production", "purge unused CSS", "FastAPI StaticFiles".
- **Relaciona com:** 3.3.
- **Exercício:** mude a cor `moss.DEFAULT` no `tailwind.config.js`, rode `make css` (ou o comando do Makefile) e recarregue a página. Depois use uma classe nova num template **sem** rodar `make css` e observe que ela não funciona — entenda por quê.

**L) Ferramentas de projeto**
- **Aprender:** Git (commits pequenos, mensagens claras), Makefile, ambientes virtuais, `requirements.txt`.
- **Pesquisar:** "conventional commits", "makefile for python projects", "pip freeze vs requirements", "ruff", "pre-commit".
- **Exercício:** adicione `ruff` ao projeto e um alvo `make lint`.

### Roteiro sugerido (ritmo tranquilo)

| Semana | Foco | Entrega |
|---|---|---|
| 1 | SQL + HTTP (A, B) | 5 consultas SQL escritas à mão no `estoque.db` |
| 2 | FastAPI async + SQLAlchemy (C, D) | A experiência `def` vs `async def` explicada em 3 frases |
| 3 | pytest + isolamento (E) | Testes de cadastro com `parametrize` |
| 4 | Concorrência + transações (F, G) | Você explica o *lost update* no papel, sem olhar |
| 5 | Camadas + config + migrações (H, I) | Nova coluna com migração e regra no serviço |
| 6 | Integridade + front + ferramentas (J, K, L) | Tela `/historico` + `make lint` |

### Como explicar isso ao seu mentor
Se ele te perguntar "o que você mudou e por quê?", uma boa resposta curta:

> "Corrigi o isolamento dos testes forçando ambiente `test` antes de importar a app e removendo o `create_all` do lifespan; tratei o TOCTOU do cadastro confiando na constraint UNIQUE e capturando `IntegrityError`; troquei o CDN por Tailwind compilado localmente. Além disso, mudei as rotas para `def` porque o SQLAlchemy é síncrono, tornei o saldo atômico com um `UPDATE` condicional (`WHERE quantidade >= q`), extraí uma camada de serviço, adicionei configuração por variáveis de ambiente e Alembic, e tornei o histórico imutável com soft delete e bloqueio de update/delete em `Movimentacao`. Validei com testes de concorrência usando threads."

E esteja preparado para as perguntas de acompanhamento: *"por que `def` e não SQLAlchemy async?"*, *"o que garante o saldo nunca ficar negativo?"* (o `WHERE quantidade >= q` no mesmo UPDATE) e *"como você testou concorrência?"* (`threading.Barrier` para largar todas as threads juntas).

---

## 9. Mini-glossário

| Termo | Significado simples |
|---|---|
| **Race condition** | Resultado depende de quem "chega primeiro" quando duas coisas acontecem ao mesmo tempo |
| **TOCTOU** | *Time Of Check To Time Of Use*: checar algo e usar depois, sem garantir que continua verdadeiro |
| **Lost update** | Duas pessoas leem o mesmo valor, cada uma grava o seu, e uma das alterações é perdida |
| **Atômico** | Indivisível: acontece por inteiro ou não acontece, e ninguém vê o "meio" |
| **Transação** | Grupo de operações no banco tratado como uma só (tudo ou nada) |
| **ACID** | As 4 garantias de um banco confiável: Atomicidade, Consistência, Isolamento, Durabilidade |
| **Constraint** | Regra que o banco impõe (ex.: `UNIQUE`, `NOT NULL`, `FOREIGN KEY`) |
| **Rollback** | Desfazer tudo o que a transação atual fez |
| **Migração** | Script versionado que leva o schema do banco de uma versão para a próxima |
| **Schema** | A estrutura do banco: tabelas, colunas, tipos, relações |
| **ORM** | Ferramenta (SQLAlchemy) que deixa você usar classes Python em vez de escrever SQL |
| **Event loop** | O "garçom único" do `async`: alterna entre tarefas que estão esperando |
| **Bloqueante** | Código que fica parado esperando (ex.: consulta ao banco síncrona) |
| **Service layer** | Camada onde ficam as regras de negócio, separada de HTTP e de banco |
| **Soft delete** | "Excluir" marcando como inativo em vez de apagar a linha |
| **Append-only** | Só se acrescenta; nunca se altera ou apaga o que já foi gravado |
| **Imutável** | Que não pode ser modificado depois de criado |
| **CDN** | Servidor externo que entrega arquivos (ex.: CSS/JS) pela internet |
| **Fixture (pytest)** | Preparação reutilizável para testes (ex.: criar um banco temporário) |
| **Fail fast** | Falhar cedo e com mensagem clara, em vez de seguir com dados errados |
| **EAFP / LBYL** | "Faça e trate o erro" / "Olhe antes de pular" — estilos de programar em Python |
