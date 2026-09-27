# Projeto Estoque

Sistema web local de controle de estoque para pequenos negócios/uso pessoal: cadastro de produtos, registro de movimentações de entrada e saída, controle de preço de compra e venda, e alerta visual quando um produto atinge o estoque mínimo. Roda inteiramente na sua máquina, sem depender de serviços externos — os dados ficam num arquivo SQLite local. O projeto também inclui um script à parte que usa a API da Anthropic (Claude) como assistente de texto livre para dúvidas sobre gestão de estoque.

## 🚀 Começando

Essas instruções permitem rodar uma cópia do projeto na sua máquina local para desenvolvimento e uso.

Este é um projeto local/pessoal — não há um ambiente de produção na nuvem. Veja **[Implantação](#-implanta%C3%A7%C3%A3o)** para notas sobre como mantê-lo rodando continuamente na própria máquina.

### 📋 Pré-requisitos

- **Python 3.10+** (testado com 3.13)
- **pip** (vem com o Python)
- Uma **chave de API da Anthropic** (`ANTHROPIC_API_KEY`) — necessária apenas para o script `main.py` (assistente via Claude); o sistema web de estoque não depende dela.

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

(Opcional) Configure a chave da Anthropic, só se for usar o assistente:

```powershell
$env:ANTHROPIC_API_KEY = "sk-ant-..."
```

Suba o sistema de estoque:

```powershell
uvicorn app.main:app --reload
```

Abra **http://127.0.0.1:8000** no navegador. Na primeira execução, o arquivo `estoque.db` (SQLite) é criado automaticamente — cadastre um produto pela própria interface para ver o fluxo completo (cadastro → movimentação de entrada/saída → alerta de estoque baixo quando a quantidade cai no mínimo).

## ⚙️ Executando os testes

```powershell
pytest
```

### 🔩 Analise os testes de ponta a ponta

Os testes em `tests/` usam o `TestClient` do FastAPI para simular requisições HTTP reais contra as rotas da aplicação (cadastro, movimentação, exclusão), com um banco SQLite temporário e isolado por teste (via `dependency_overrides` — nunca tocam no `estoque.db` real). Eles cobrem os fluxos essenciais do sistema:

```
tests/test_produtos.py
  - cadastro de produto aparece na listagem
  - SKU duplicado é rejeitado
  - exclusão remove o produto

tests/test_movimentacoes.py
  - saída maior que o estoque disponível é rejeitada
  - alerta de estoque baixo liga/desliga conforme a quantidade
```

### ⌨️ E testes de estilo de codificação

Ainda não há linter/formatter configurado neste repositório (sem `ruff`, `black` ou `mypy` até o momento) — é um projeto em estágio inicial. Ao adicionar um, o comando de verificação entraria aqui, por exemplo:

```
ruff check .
```

## 📦 Implantação

Não há um ambiente de produção/nuvem para este projeto — ele foi desenhado para rodar localmente, para um único usuário. Para deixá-lo rodando continuamente na sua própria máquina (sem `--reload`, mais adequado a uso "fixo"):

```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## 🛠️ Construído com

* [FastAPI](https://fastapi.tiangolo.com/) - Framework web
* [SQLAlchemy](https://www.sqlalchemy.org/) - ORM (estilo 2.0, `Mapped`/`mapped_column`)
* [SQLite](https://www.sqlite.org/) - Banco de dados local
* [Jinja2](https://jinja.palletsprojects.com/) - Renderização de HTML no servidor
* [Tailwind CSS](https://tailwindcss.com/) (via CDN) - Estilização
* [pytest](https://docs.pytest.org/) + [httpx](https://www.python-httpx.org/) - Testes automatizados
* [Anthropic SDK](https://github.com/anthropics/anthropic-sdk-python) - Assistente via Claude (`main.py`)

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
