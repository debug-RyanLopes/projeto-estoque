# projeto-estoque

## Setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:ANTHROPIC_API_KEY = "sk-ant-..."
```

## Run

**AI assistant script:**

```powershell
python main.py "How should I organize SKUs for a small warehouse?"
```

**Stock control web app** (cadastro de produtos, movimentação, alerta de estoque baixo):

```powershell
uvicorn app.main:app --reload
```

Abra http://127.0.0.1:8000 no navegador. Os dados ficam em `estoque.db` (SQLite, criado automaticamente na primeira execução).

## Rodando os testes

```powershell
pytest
```

Os testes usam um banco SQLite temporário isolado (via `dependency_overrides`) — nunca tocam em `estoque.db`.
