# Variáveis
# Dica: para usar o venv sem ativá-lo, rode: make run PYTHON=.venv/Scripts/python
PYTHON = python
APP = app.main:app

.PHONY: help install migrate run test css clean stop

# Comando padrão
help:
	@echo "Comandos disponiveis:"
	@echo "  make install - Instala as dependencias do projeto"
	@echo "  make migrate - Cria/atualiza o banco (alembic upgrade head)"
	@echo "  make run     - Aplica as migracoes e executa o servidor Web com reload automatico"
	@echo "  make test    - Executa os testes automatizados"
	@echo "  make css     - Regenera o CSS local do Tailwind (precisa de Node.js)"
	@echo "  make clean   - Remove caches temporarios do Python e do pytest"
	@echo "  make stop    - Encerra a aplicacao rodando na porta 8000"

install:
	$(PYTHON) -m pip install -r requirements.txt

migrate:
	$(PYTHON) -m alembic upgrade head

run: migrate
	$(PYTHON) -m uvicorn $(APP) --reload

test:
	$(PYTHON) -m pytest

css:
	npx --yes tailwindcss@3.4.17 -c tailwind.config.js -i app/static/css/input.css -o app/static/css/tailwind.css --minify

clean:
	@powershell -NoProfile -Command "Get-ChildItem -Recurse -Directory -Force | Where-Object { $$_.Name -in ('__pycache__','.pytest_cache') -and $$_.FullName -notlike '*\.venv\*' } | Remove-Item -Recurse -Force"

stop:
	@echo "Encerrando a aplicacao na porta 8000..."
	@powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $$_.OwningProcess -Force -ErrorAction SilentlyContinue }; exit 0"
