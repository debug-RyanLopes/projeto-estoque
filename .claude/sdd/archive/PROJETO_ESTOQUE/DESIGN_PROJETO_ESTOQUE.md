# DESIGN: Projeto Estoque

> Technical design for implementing Projeto Estoque

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | PROJETO_ESTOQUE |
| **Date** | 2026-09-26 |
| **Author** | design-agent |
| **DEFINE** | [DEFINE_PROJETO_ESTOQUE.md](./DEFINE_PROJETO_ESTOQUE.md) |
| **Status** | ✅ Shipped |

---

## Architecture Overview

O MVP já está implementado e testado manualmente (ver DEFINE). Este design documenta a arquitetura existente, formaliza duas correções de padrão (modelos SQLAlchemy 2.0-style e `Numeric` para dinheiro) e planeja a cobertura de testes automatizados que hoje não existe.

```text
┌───────────────────────────────────────────────────────────────────┐
│                         SYSTEM DIAGRAM                             │
├───────────────────────────────────────────────────────────────────┤
│                                                                     │
│  [Navegador] ──HTTP (form POST/GET)──→ [FastAPI routes: main.py]  │
│                                                ↓                   │
│                                     [Depends(get_db) — session]    │
│                                                ↓                   │
│                                   [SQLAlchemy ORM: models.py]       │
│                                                ↓                   │
│                                        [SQLite: estoque.db]        │
│                                                ↓                   │
│                                  [Jinja2Templates → HTML render]    │
│                                                ↓                   │
│  [Navegador] ←── HTML (tabela de produtos + alerta visual) ────────│
│                                                                     │
└───────────────────────────────────────────────────────────────────┘
```

Sem serviços externos: um único processo Python, um único arquivo de banco local. Confirma o requisito "IaC Impact: None" da DEFINE.

---

## Components

| Component | Purpose | Technology |
|-----------|---------|------------|
| Routes (`app/main.py`) | Endpoints HTTP: dashboard, cadastro, movimentação, exclusão | FastAPI, `lifespan` para criar tabelas no boot |
| Persistência (`app/database.py`, `app/models.py`) | Sessão de banco e modelos `Produto`/`Movimentacao` | SQLAlchemy 2.0 + SQLite |
| Apresentação (`app/templates/`, `app/static/`) | Renderização HTML server-side + estilos | Jinja2 (autoescape ligado por padrão para `.html`) |
| Testes (`tests/`) | Cobertura automatizada dos Acceptance Tests da DEFINE | pytest + `TestClient` (httpx) |

---

## Key Decisions

### Decision 1: Stack web — FastAPI + Jinja2 server-rendered + SQLite

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted (já implementado) |
| **Date** | 2026-09-26 |

**Context:** Precisava de uma interface Web para um único usuário local, sem necessidade de autenticação, API pública ou múltiplos clientes (DEFINE: Target Users, Constraints).

**Choice:** FastAPI servindo HTML diretamente via Jinja2Templates; SQLite como armazenamento; sem camada JSON/API separada.

**Rationale:** Zero build step de frontend, um único processo/deploy, e alinhado ao estado atual do projeto (que hoje é um único script Python). O padrão FastAPI+Pydantic já está catalogado e validado no KB deste projeto (`python-frameworks/patterns/fastapi.md`, confidence 0.95).

**Alternatives Rejected:**
1. FastAPI como API JSON + frontend SPA separado (React/Vue) — rejeitado: dobra a complexidade (dois deploys, CORS, build de JS) para um caso de uso de um usuário só.
2. Django (monolito com admin embutido) — rejeitado: contradiz a escolha de framework já validada com o usuário, sem motivo técnico novo.

**Consequences:**
- Aceita: sem separação frontend/backend, mais difícil de expor como API pública no futuro sem refatoração.
- Ganha: menor superfície de manutenção, zero infraestrutura adicional.

---

### Decision 2: Modelos SQLAlchemy 2.0-style (`Mapped`/`mapped_column`) e `Numeric` para dinheiro

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted — ação de Build |
| **Date** | 2026-09-26 |

**Context:** O `app/models.py` atual usa o estilo legado `Column(Integer, ...)` e `Float` para `preco_compra`/`preco_venda`. O KB deste projeto (`python-frameworks/patterns/sqlalchemy.md`) documenta o estilo 2.0 (`Mapped[tipo]` + `mapped_column()`) como padrão atual, e explicitamente recomenda `Numeric`, nunca `Float`, para valores monetários — `Float` introduz erro de arredondamento binário em cálculos de preço.

**Choice:** Migrar `Produto`/`Movimentacao` para `DeclarativeBase` + `Mapped[]`/`mapped_column()`, e trocar `preco_compra`/`preco_venda` de `Float` para `Numeric(10, 2)`.

**Rationale:** Corrige um desvio real do padrão catalogado no KB antes que mais código seja escrito em cima do estilo legado; `Numeric` evita bugs sutis de arredondamento em preços (ex.: `0.1 + 0.2 != 0.3` em `float`).

**Alternatives Rejected:**
1. Manter `Float` e arredondar na exibição (`"%.2f"|format`) — rejeitado: o erro de arredondamento já existe no armazenamento/cálculo, não só na exibição; movimentações acumuladas amplificariam o erro.
2. Manter estilo `Column()` legado — rejeitado: funciona, mas mistura estilos dentro do mesmo projeto e perde tipagem estática (mypy/pyright) que `Mapped[]` dá de graça.

**Consequences:**
- Aceita: pequeno retrabalho em `models.py` e `database.py` (troca de `declarative_base()` por `class Base(DeclarativeBase)`), sem mudança de schema visível ao usuário.
- Ganha: tipagem correta, sem risco de erro de arredondamento em preços.

---

### Decision 3: Formulários HTML simples com redirect 303 (sem HTMX no MVP)

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted (já implementado) |
| **Date** | 2026-09-26 |

**Context:** A abordagem de brainstorm original cogitava HTMX para atualização parcial de página. Para chegar a uma versão funcional rapidamente, o MVP implementado usa apenas formulários HTML padrão com redirect 303 pós-POST.

**Choice:** Manter formulários simples + redirect no MVP; documentar HTMX como incremento futuro (já listado como COULD na DEFINE).

**Rationale:** Reduz uma dependência de frontend a mais sem abrir mão do modelo server-rendered; a UX de reload completo é aceitável para um único usuário local com poucos produtos.

**Alternatives Rejected:**
1. Implementar HTMX agora — rejeitado por YAGNI: não é um MUST da DEFINE, e adicionar agora atrasaria a entrega do MVP sem ganho funcional.

**Consequences:**
- Aceita: cada ação recarrega a página inteira.
- Ganha: menos uma biblioteca/JS para manter; migração para HTMX depois não exige mudar a arquitetura de fundo (mesmas rotas, só trocaria o retorno de HTML completo por fragmentos).

---

### Decision 4: Erros de domínio (SKU duplicado, estoque insuficiente) via redirect + banner; erros inesperados via `HTTPException`

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted (já implementado) |
| **Date** | 2026-09-26 |

**Context:** O site é navegado via formulários HTML puros (sem JS/fetch). Um `HTTPException` padrão do FastAPI devolve um JSON cru (`{"detail": "..."}`), o que é uma péssima UX para um usuário navegando por formulários.

**Choice:** Erros de validação de negócio esperados (SKU duplicado, saída maior que o estoque) fazem `RedirectResponse` para `/?erro=<mensagem>`, renderizado como banner na página. Erros que não deveriam acontecer em uso normal (produto inexistente por id) continuam como `HTTPException(404)`.

**Rationale:** Mantém a experiência 100% dentro do fluxo HTML para os casos que o usuário realmente vai encontrar (chegou perto do KB checklist: "Erros de domínio viram HTTPException ou exception handler — nunca vazam stack trace cru para o cliente" — aqui vão um passo além ao renderizar no próprio HTML em vez de JSON, por não haver client JS consumindo a API).

**Alternatives Rejected:**
1. Exception handler global retornando JSON (`JSONResponse`) para `EstoqueInsuficienteError`/SKU duplicado — rejeitado: ainda seria JSON cru numa navegação HTML pura.

**Consequences:**
- Aceita: mensagem de erro trafega via query string (visível na URL, sem dado sensível).
- Ganha: banner de erro amigável sem precisar de JavaScript.

---

## File Manifest

| # | File | Action | Purpose | Agent | Dependencies |
|---|------|--------|---------|-------|--------------|
| 1 | `app/database.py` | Modify | `Base` como `DeclarativeBase` (2.0-style) | @python-improver | None |
| 2 | `app/models.py` | Modify | `Mapped`/`mapped_column`; `preco_compra`/`preco_venda` → `Numeric(10,2)` | @python-improver | 1 |
| 3 | `app/main.py` | Verify (sem mudança esperada) | Confirmar que rotas continuam corretas após a troca de tipo em `models.py` | @code-reviewer | 2 |
| 4 | `requirements.txt` | Modify | Adicionar `pytest`, `httpx` (TestClient) | (general) | None |
| 5 | `tests/conftest.py` | Create | Fixture `client` com banco SQLite de teste isolado via `dependency_overrides` | @test-generator | 1, 2, 4 |
| 6 | `tests/test_produtos.py` | Create | AT-001 (cadastro), AT-002 (SKU duplicado), AT-005 (exclusão) | @test-generator | 5 |
| 7 | `tests/test_movimentacoes.py` | Create | AT-003 (saída > estoque), AT-004 (alerta liga/desliga) | @test-generator | 5 |
| 8 | `README.md` | Modify | Seção "Rodando os testes" (`pytest`) | (general) | 5, 6, 7 |

**Total Files:** 8

---

## Agent Assignment Rationale

> Agentes descobertos em `.claude/agents/**/*.md` — Build phase invoca os especialistas casados abaixo.

| Agent | Files Assigned | Why This Agent |
|-------|----------------|-----------------|
| @python-improver | 1, 2 | Descrição: "review and improve Python code — readability, idiomatic style, correctness... Not for adding new features from scratch — it improves existing code." Exatamente o caso: código já funciona, só precisa ser alinhado ao padrão 2.0-style do KB. |
| @code-reviewer | 3 | "Expert code review specialist ensuring quality, security, and maintainability" — usado para *verificar* `main.py` após a mudança de tipos em `models.py`, não para reescrever. |
| @test-generator | 5, 6, 7 | "Test automation expert for Python. Generates pytest unit tests, integration tests, and fixtures." Casa diretamente com o KB domain `testing` (fixture-factories, integration-tests) apontado na DEFINE. |
| (general) | 4, 8 | Edições triviais de arquivo texto (lista de dependências, um parágrafo de README) — não justificam um especialista dedicado. |

**Agent Discovery:**
- Scanned: `.claude/agents/**/*.md` (63 agentes)
- Matched by: purpose keywords ("melhorar código existente" vs "gerar testes"), KB domain (`testing` → test-generator)

---

## Code Patterns

### Pattern 1: Modelos 2.0-style com `Numeric` para dinheiro

```python
# app/database.py — de .claude/kb/python-frameworks/patterns/sqlalchemy.md
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = "sqlite:///./estoque.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

```python
# app/models.py
from datetime import datetime

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Produto(Base):
    __tablename__ = "produtos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(200))
    sku: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    preco_compra: Mapped[float] = mapped_column(Numeric(10, 2))
    preco_venda: Mapped[float] = mapped_column(Numeric(10, 2))
    estoque_minimo: Mapped[int] = mapped_column(default=0)
    quantidade: Mapped[int] = mapped_column(default=0)

    movimentacoes: Mapped[list["Movimentacao"]] = relationship(
        back_populates="produto", cascade="all, delete-orphan"
    )


class Movimentacao(Base):
    __tablename__ = "movimentacoes"

    id: Mapped[int] = mapped_column(primary_key=True)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"))
    tipo: Mapped[str] = mapped_column(String(10))  # "entrada" ou "saida"
    quantidade: Mapped[int]
    data: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    produto: Mapped["Produto"] = relationship(back_populates="movimentacoes")
```

### Pattern 2: Fixture de teste com banco isolado (`dependency_overrides`)

```python
# tests/conftest.py — adapta .claude/kb/testing/patterns/integration-tests.md
# ao caso FastAPI + SQLAlchemy: banco de teste isolado via dependency_overrides
# em vez do banco real (estoque.db).
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app


@pytest.fixture
def client(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'test.db'}",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
```

### Pattern 3: Teste de acceptance test (AT-003 — saída maior que o estoque)

```python
# tests/test_movimentacoes.py
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
```

---

## Data Flow

```text
1. Navegador envia POST /produtos ou /movimentacoes (form-urlencoded)
   │
   ▼
2. FastAPI valida os campos via Annotated[..., Form(...)] (tipo, ge=0, gt=0)
   │
   ▼
3. Depends(get_db) abre uma Session (fecha automaticamente após a resposta)
   │
   ▼
4. Regra de negócio: valida SKU único / estoque suficiente antes de persistir
   │
   ▼
5. Commit no SQLite; RedirectResponse 303 para "/" (ou "/?erro=..." em caso de erro esperado)
   │
   ▼
6. GET / consulta produtos ordenados por nome e renderiza via Jinja2
   (autoescape ativo por padrão para templates .html — sem risco de XSS via nome/SKU)
```

---

## Integration Points

| External System | Integration Type | Authentication |
|-----------------|-------------------|-----------------|
| Nenhum | N/A | N/A — app local self-contained, sem dependências externas (confirma "IaC Impact: None" da DEFINE) |

---

## Testing Strategy

| Test Type | Scope | Files | Tools | Coverage Goal |
|-----------|-------|-------|-------|----------------|
| Integration (API) | Rotas FastAPI + SQLite de teste | `tests/test_produtos.py`, `tests/test_movimentacoes.py` | pytest + `TestClient` (httpx) | Cobrir AT-001 a AT-005 |
| Manual/E2E | Fluxo completo no navegador | - | Manual (já validado nesta sessão via curl) | Happy path + alerta visual |

Mapeamento explícito Acceptance Test → teste automatizado:

| Acceptance Test (DEFINE) | Teste automatizado |
|--------------------------|----------------------|
| AT-001 (cadastro + listagem) | `test_produtos.py::test_cadastro_aparece_na_listagem` |
| AT-002 (SKU duplicado) | `test_produtos.py::test_sku_duplicado_e_rejeitado` |
| AT-003 (saída > estoque) | `test_movimentacoes.py::test_saida_maior_que_estoque_e_rejeitada` |
| AT-004 (alerta liga/desliga) | `test_movimentacoes.py::test_alerta_estoque_baixo_liga_desliga` |
| AT-005 (exclusão) | `test_produtos.py::test_exclusao_remove_produto` |

---

## Error Handling

| Error Type | Handling Strategy | Retry? |
|------------|---------------------|--------|
| SKU duplicado no cadastro | Redirect 303 para `/?erro=...`, banner exibido na página | Não (usuário corrige o SKU e reenvia) |
| Saída maior que o estoque disponível | Redirect 303 com mensagem informando quantidade disponível | Não (usuário ajusta a quantidade) |
| Produto inexistente (id inválido em movimentação/exclusão) | `HTTPException(404)` | Não — não deveria ocorrer em uso normal via UI |
| Campos de formulário inválidos (tipo errado, negativo) | Validação automática do FastAPI (`Form(ge=0)` etc.) → `422` | Não |

---

## Configuration

| Config Key | Type | Default | Description |
|------------|------|---------|--------------|
| `DATABASE_URL` | string | `sqlite:///./estoque.db` | Caminho do arquivo SQLite; testes usam um banco temporário via `tmp_path`, nunca o arquivo real |

---

## Security Considerations

- Sem autenticação/login — aceito por decisão explícita (DEFINE, Assumption A-001): app local, single-user, nunca exposto à internet.
- Sem risco de SQL injection: todo acesso a dados passa pelo ORM (SQLAlchemy), sem SQL cru concatenado.
- Sem risco de XSS via dados do usuário (nome de produto, SKU): Jinja2Templates tem autoescape ativo por padrão para arquivos `.html`.
- Mensagem de erro trafega em query string (`?erro=...`) — aceitável pois nunca contém dado sensível, só texto de validação (ex.: "SKU já cadastrado").
- CSRF: fora de escopo — não há sessão/cookie de autenticação para um atacante forjar.

---

## Observability

| Aspect | Implementation |
|--------|------------------|
| Logging | Log de acesso padrão do `uvicorn` (suficiente para uso local single-user) |
| Metrics | Não aplicável — fora de escopo (YAGNI, sem usuários concorrentes a monitorar) |
| Tracing | Não aplicável — mesmo motivo |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|-----------|
| 1.0 | 2026-09-26 | design-agent | Versão inicial — documenta a arquitetura já implementada e planeja o gap de testes automatizados + correção de padrão SQLAlchemy 2.0/Numeric |
| 1.1 | 2026-09-26 | ship-agent | Shipped and archived |

---

## Next Step

**Ready for:** `/ship .claude/sdd/features/DEFINE_PROJETO_ESTOQUE.md`
