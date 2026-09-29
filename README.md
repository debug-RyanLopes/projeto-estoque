# Projeto Estoque

Sistema web local de controle de estoque para pequenos negócios/uso pessoal: cadastro de produtos (com estoque inicial), registro de movimentações de entrada e saída, histórico de movimentações (seção recolhível na tela), controle de preço de compra e venda, e alerta visual quando um produto atinge o estoque mínimo. Roda inteiramente na sua máquina, sem depender de serviços externos — os dados ficam num arquivo SQLite local.

## 🚀 Começando

Essas instruções permitem rodar uma cópia do projeto na sua máquina local para desenvolvimento e uso.

Este é um projeto local/pessoal — não há um ambiente de produção na nuvem. Veja **[Implantação](#-implanta%C3%A7%C3%A3o)** para notas sobre como mantê-lo rodando continuamente na própria máquina.

### 📋 Pré-requisitos

- **Python 3.10+** (testado com 3.13)
- **pip** (vem com o Python)

```powershell
python --version
```

### 🔧 Instalação

Clone o repositório e entre na pasta:

```powershell
git clone https://github.com/debug-RyanLopes/projeto-estoque.git
cd projeto-estoque
```

Crie e ative um ambiente virtual:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Instale as dependências:

```powershell
pip install -r requirements.txt
```

Crie/atualize o banco com as migrações (Alembic) e suba o sistema de estoque:

```powershell
alembic upgrade head
uvicorn app.main:app --reload
```

(ou simplesmente `make run`, que faz os dois passos.) Bancos `estoque.db` criados por versões anteriores são atualizados sem perda de dados.

Abra **http://127.0.0.1:8000** no navegador. O arquivo `estoque.db` (SQLite) é criado pela migração — cadastre um produto pela própria interface para ver o fluxo completo (cadastro → movimentação de entrada/saída → alerta de estoque baixo quando a quantidade cai no mínimo).

### 🔧 Configuração por ambiente

A configuração vem de variáveis de ambiente (`app/config.py`):

| Variável | Padrão | Descrição |
|---|---|---|
| `APP_ENV` | `dev` | `dev`, `test` ou `prod` — escolhe o banco padrão |
| `DATABASE_URL` | `sqlite:///./estoque.db` (`estoque.test.db` em `test`) | Sobrescreve a URL do banco |

### 🗃️ Migrações

O schema do banco é versionado em `migrations/` (Alembic). Depois de alterar `app/models.py`:

```powershell
alembic revision --autogenerate -m "descrição da mudança"
alembic upgrade head
```

## ⚙️ Executando os testes

```powershell
pytest
```

### 🔩 Analise os testes de ponta a ponta

Os testes em `tests/` usam o `TestClient` do FastAPI para simular requisições HTTP reais contra as rotas da aplicação (cadastro, movimentação, exclusão), com um banco SQLite temporário e isolado por teste. O `tests/conftest.py` força `APP_ENV=test` e um banco descartável *antes* de importar a aplicação, então a suíte nunca cria nem altera o `estoque.db` real. Eles cobrem os fluxos essenciais do sistema:

```
tests/test_produtos.py
  - cadastro de produto aparece na listagem
  - quantidade inicial define o saldo e gera uma entrada no histórico
  - SKU duplicado é rejeitado
  - exclusão remove o produto

tests/test_movimentacoes.py
  - saída maior que o estoque disponível é rejeitada
  - alerta de estoque baixo liga/desliga conforme a quantidade
  - histórico lista entradas e saídas, mais recentes primeiro

tests/test_servicos.py
  - saídas simultâneas nunca deixam o estoque negativo (atomicidade)
  - cadastro simultâneo do mesmo SKU gera um único produto (sem erro 500)
  - movimentações são imutáveis; excluir produto preserva o histórico

tests/test_infra.py
  - a suíte nunca aponta para o banco real
  - as migrações produzem o mesmo schema dos modelos
  - a página usa CSS local, sem CDN
```

### ⌨️ E testes de estilo de codificação

Ainda não há linter/formatter configurado neste repositório (sem `ruff`, `black` ou `mypy` até o momento) — é um projeto em estágio inicial. Ao adicionar um, o comando de verificação entraria aqui, por exemplo:

```
ruff check .
```

## 📦 Implantação

Não há um ambiente de produção/nuvem para este projeto — ele foi desenhado para rodar localmente, para um único usuário. Para deixá-lo rodando continuamente na sua própria máquina (sem `--reload`, mais adequado a uso "fixo"):

```powershell
alembic upgrade head
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## 🛠️ Construído com

* [FastAPI](https://fastapi.tiangolo.com/) - Framework web
* [SQLAlchemy](https://www.sqlalchemy.org/) - ORM (estilo 2.0, `Mapped`/`mapped_column`)
* [Alembic](https://alembic.sqlalchemy.org/) - Migrações de banco de dados
* [SQLite](https://www.sqlite.org/) - Banco de dados local
* [Jinja2](https://jinja.palletsprojects.com/) - Renderização de HTML no servidor
* [Tailwind CSS](https://tailwindcss.com/) - Estilização, com CSS gerado localmente em `app/static/css/tailwind.css` (sem CDN; para regenerar após mudar os templates: `make css`, requer Node.js)
* [pytest](https://docs.pytest.org/) + [httpx](https://www.python-httpx.org/) - Testes automatizados

## 🖇️ Colaborando

Projeto pessoal, mas sugestões são bem-vindas — abra uma [issue](https://github.com/debug-RyanLopes/projeto-estoque/issues) ou um pull request.

## 📌 Versão

Ainda não há releases/tags publicadas neste repositório. Acompanhe o histórico em [commits](https://github.com/debug-RyanLopes/projeto-estoque/commits).

## ✒️ Autores

* **Ryan Lopes** - *Desenvolvimento* - [debug-RyanLopes](https://github.com/debug-RyanLopes)

## 📄 Licença

Nenhuma licença definida até o momento.

## 🎁 Expressões de gratidão

* Conte a outras pessoas sobre este projeto 📢;
* Um agradecimento publicamente 🫂;
* etc.

---
⌨️ com ❤️ por [Ryan Lopes](https://github.com/debug-RyanLopes) 😊
