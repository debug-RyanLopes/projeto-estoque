# Knowledge Base — Índice Geral

> Base de conhecimento sobre Python e frameworks, para uso por agentes deste projeto
> (ex.: [python-code-improver](../agentes/python-code-improver.md)).

## Como resolver conhecimento (KB-first)

1. Ler o `index.md` do domínio relevante abaixo — só os títulos, não o conteúdo inteiro.
2. Carregar sob demanda apenas o arquivo específico (`concepts/` ou `patterns/`) que casa
   com a tarefa em mãos — nunca o domínio inteiro.
3. Se a KB não cobrir o caso, tratar como lacuna e verificar com o usuário ou com
   documentação oficial (não inventar comportamento de API).

## Domínios

| Domínio | Caminho | Cobertura |
|---|---|---|
| Python (core) | [python-core/index.md](python-core/index.md) | Idiomas, tipagem, erros/recursos, concorrência/performance, testes, empacotamento |
| Frameworks | [frameworks/index.md](frameworks/index.md) | FastAPI, Flask, Django, SQLAlchemy, Pydantic, pandas |

## Convenção de arquivos

- `index.md` — mapa de tópicos do domínio (cabeçalhos apenas, leitura rápida).
- `quick-reference.md` — tabela de decisão / cheat sheet para consulta rápida.
- `concepts/*.md` — explicação de um conceito isolado, com exemplos mínimos.
- `patterns/*.md` — padrão de implementação completo, com código pronto para adaptar.

## Escopo e limites

- Cobre versões atuais e estáveis das ferramentas (Python 3.11+, Pydantic v2,
  SQLAlchemy 2.0-style, FastAPI/Django/Flask recentes). Projetos presos em versões
  antigas devem tratar o conteúdo aqui como referência, não como verdade absoluta —
  conferir a versão instalada antes de aplicar um padrão.
- Não cobre infraestrutura, deploy, ou APIs de terceiros não-Python.
- Não existe (ainda) um domínio `shared/` — `_template.md` referencia
  `.claude/kb/shared/component-model.md` e um `anti_pattern_refs: [shared-anti-patterns]`
  para o framework de autoria de agentes em si (tiers T1/T2/T3, `agent-architect`,
  `spec-linter`). Esse domínio é sobre *como criar agentes*, não sobre Python/frameworks,
  e não foi criado aqui — não inventamos conteúdo para uma ferramenta que não existe
  neste projeto. Se esse framework existir em outro lugar, apontar aqui.
