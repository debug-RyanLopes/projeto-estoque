# DEFINE: Projeto Estoque

> Sistema web local de controle de estoque — cadastro de produtos, movimentação de entrada/saída e alerta de estoque baixo.

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | PROJETO_ESTOQUE |
| **Date** | 2026-09-26 |
| **Author** | define-agent |
| **Status** | ✅ Shipped |
| **Clarity Score** | 14/15 |

---

## Problem Statement

O usuário não tem nenhum controle estruturado do estoque de produtos: sem cadastro centralizado, sem registro de entradas/saídas, sem visibilidade de quando um item está acabando e sem rastreio de preço de compra vs. venda para calcular margem.

---

## Target Users

| User | Role | Pain Point |
|------|------|------------|
| Ryan Lopes (dono/operador) | Único usuário, uso pessoal/local | Não sabe quanto tem de cada produto em tempo real, corre risco de vender sem ter estoque disponível e não tem registro de preço de compra/venda por item |

---

## Goals

What success looks like (prioritized):

| Priority | Goal |
|----------|------|
| **MUST** | Cadastrar produtos com nome, SKU único, preço de compra, preço de venda e estoque mínimo |
| **MUST** | Registrar movimentações de entrada e saída que atualizam a quantidade em estoque |
| **MUST** | Impedir saída de quantidade maior que o estoque disponível |
| **MUST** | Exibir alerta visual quando a quantidade de um produto cair para o estoque mínimo ou abaixo |
| **SHOULD** | Permitir excluir um produto cadastrado |
| **SHOULD** | Persistir os dados localmente entre execuções (sem precisar recadastrar tudo a cada reinício) |
| **COULD** | Editar campos de um produto já cadastrado (hoje só cadastro + exclusão) |
| **COULD** | Tela de histórico de movimentações (hoje gravado no banco, sem tela dedicada) |
| **COULD** | Atualização parcial de página (HTMX) em vez de reload completo |
| **COULD** | Autenticação / múltiplos usuários |
| **COULD** | Notificação ativa (e-mail) de estoque baixo, além do alerta visual |

**Priority Guide:**
- **MUST** = MVP fails without this
- **SHOULD** = Important, but workaround exists
- **COULD** = Nice-to-have, cut first if needed

---

## Success Criteria

Measurable outcomes:

- [x] Cadastro de produto reflete na listagem imediatamente (validado manualmente nesta sessão via requisições HTTP)
- [x] SKU duplicado é rejeitado com mensagem de erro visível na tela (validado)
- [x] Saída de quantidade maior que o estoque disponível é rejeitada com mensagem informando a quantidade disponível (validado)
- [x] Produto com quantidade ≤ estoque mínimo aparece destacado visualmente (linha vermelha + ⚠️) em 100% dos casos testados; some do destaque assim que a quantidade volta a ficar acima do mínimo (validado)
- [ ] Sistema roda com um único comando (`uvicorn app.main:app`) sem depender de infraestrutura externa (banco de dados é um arquivo SQLite local) — funcional, mas ainda não documentado como critério formal de aceite em ambiente limpo

---

## Acceptance Tests

| ID | Scenario | Given | When | Then |
|----|----------|-------|------|------|
| AT-001 | Cadastro + listagem (happy path) | Nenhum produto cadastrado | Usuário envia formulário de cadastro com nome, SKU, preços e estoque mínimo | Produto aparece na tabela com quantidade inicial 0 |
| AT-002 | SKU duplicado | Produto com SKU "X" já existe | Usuário tenta cadastrar outro produto com SKU "X" | Cadastro é rejeitado e mensagem "SKU já cadastrado" é exibida; nenhum registro duplicado é criado |
| AT-003 | Saída maior que o disponível | Produto tem quantidade 3 | Usuário registra saída de 100 unidades | Movimentação é rejeitada, mensagem informa a quantidade disponível, e a quantidade do produto permanece 3 |
| AT-004 | Alerta de estoque baixo liga/desliga | Produto com estoque mínimo 5 e quantidade 3 | Usuário registra entrada de 10 unidades (quantidade final 13) | A linha do produto deixa de ser destacada como "baixo" |
| AT-005 | Exclusão de produto | Produto cadastrado existe | Usuário aciona exclusão | Produto some da listagem e suas movimentações associadas são removidas (cascade) |

---

## Out of Scope

Explicitly NOT included nesta versão:

- Autenticação, login ou múltiplos usuários com permissões diferentes (confirmado: uso pessoal, local, single-user)
- Notificação ativa de estoque baixo (e-mail, push) — só alerta visual na tela
- API pública ou app separado consumindo os dados via JSON (a UI é a única interface)
- Deploy em nuvem, multi-tenant ou banco de dados servidor (Postgres) — decisão explícita por SQLite local
- Edição de produto já cadastrado (só cadastro e exclusão existem hoje)
- Tela de histórico de movimentações (os dados são gravados na tabela `movimentacoes`, mas não há relatório/visualização ainda)
- Relatórios financeiros (margem, DRE, curva ABC etc.) além do armazenamento simples de preço de compra e venda por produto

---

## Constraints

| Type | Constraint | Impact |
|------|------------|--------|
| Technical | Stack já decidida e implementada: FastAPI + SQLAlchemy + Jinja2 (server-rendered) + SQLite, sem autenticação | Design deve documentar/formalizar a arquitetura existente, não reabrir a escolha de stack |
| Technical | Formulários HTML simples com redirect 303 (sem HTMX ainda), decisão consciente para reduzir complexidade no MVP | HTMX pode ser adicionado depois sem mudar a arquitetura de fundo |
| Resource | Uso local/pessoal, sem orçamento ou necessidade de infraestrutura de deploy | Nenhum trabalho de IaC ou cloud é necessário nesta fase |

---

## Technical Context

> Essential context for Design phase - prevents misplaced files and missed infrastructure needs.

| Aspect | Value | Notes |
|--------|-------|-------|
| **Deployment Location** | `app/` (já existe: `app/main.py`, `app/models.py`, `app/database.py`, `app/templates/`, `app/static/`) | Design deve manter esta estrutura, não recriar do zero |
| **KB Domains** | `python-frameworks` (padrão `fastapi`, confidence 0.95, source-verificado nesta sessão; padrão `sqlalchemy`, confidence 0.70, hand-authored), `pydantic`, `python` (clean-architecture, error-handling), `testing` (para a lacuna de testes automatizados, ainda inexistentes) | fastapi.md foi validado contra docs oficiais (FastAPI 0.141.1, Pydantic 2.9+) nesta sessão |
| **IaC Impact** | None | SQLite é um arquivo local (`estoque.db`), sem servidor de banco ou infraestrutura cloud |

**Why This Matters:**

- **Location** → Design phase uses correct project structure, prevents misplaced files
- **KB Domains** → Design phase pulls correct patterns from KB
- **IaC Impact** → Triggers infrastructure planning, avoids "works locally" failures

---

## Assumptions

Assumptions that if wrong could invalidate the design:

| ID | Assumption | If Wrong, Impact | Validated? |
|----|------------|------------------|------------|
| A-001 | O sistema permanecerá single-user/local (sem necessidade de login) | Precisaria adicionar autenticação, sessões e possivelmente trocar SQLite por um banco com melhor suporte a concorrência | [x] Confirmado pelo usuário durante o brainstorm |
| A-002 | O volume de produtos e movimentações é pequeno (dezenas a centenas de linhas) | SQLite deixaria de ser suficiente; precisaria migrar para Postgres/MySQL | [ ] |
| A-003 | Alerta visual na própria tela é suficiente, sem necessidade de notificação ativa | Precisaria adicionar envio de e-mail/push e a infraestrutura associada | [x] Confirmado pelo usuário durante o brainstorm |
| A-004 | Não há necessidade de editar produtos já cadastrados no curto prazo | Precisaria adicionar tela/endpoint de edição antes do esperado | [ ] |

**Note:** Validate critical assumptions before DESIGN phase. Unvalidated assumptions become risks.

---

## Clarity Score Breakdown

| Element | Score (0-3) | Notes |
|---------|-------------|-------|
| Problem | 3 | Problema específico e já demonstrado com código funcional nesta sessão |
| Users | 2 | Persona única e clara (uso pessoal/local), mas é um único usuário genérico — não há múltiplos perfis a detalhar |
| Goals | 3 | MoSCoW completo, todo MUST já implementado e testado |
| Success | 3 | Critérios mensuráveis, a maioria já validada manualmente via testes HTTP nesta sessão |
| Scope | 3 | Out of scope explícito e extenso, fronteiras claras |
| **Total** | **14/15** | |

**Scoring Guide:**
- 0 = Missing entirely
- 1 = Vague or incomplete
- 2 = Clear but missing details
- 3 = Crystal clear, actionable

**Minimum to proceed: 12/15**

---

## Open Questions

- Nenhuma bloqueante para /design. Pontos que o Design pode formalizar: se/quando adicionar edição de produtos (A-004), e se o histórico de movimentações (COULD) entra num incremento futuro.

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-09-26 | define-agent | Versão inicial — requisitos extraídos da sessão de brainstorm conversacional e do MVP já implementado e testado manualmente (sem BRAINSTORM.md formal, pois o usuário optou por pular direto para a implementação) |
| 1.1 | 2026-09-26 | ship-agent | Shipped and archived |

---

## Next Step

**Ready for:** `/ship .claude/sdd/features/DEFINE_PROJETO_ESTOQUE.md`
