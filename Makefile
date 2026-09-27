# Variáveis
PYTHON = python
UVICORN = uvicorn
APP = app.main:app

# Comando padrão
.PHONY: help install run test clean stop

help:
	@echo "Comandos disponíveis:"
	@echo "  make install - Instala as dependências do projeto"
	@echo "  make run     - Executa o servidor Web com reload automático"
	@echo "  make test    - Executa os testes automatizados"
	@echo "  make clean   - Remove arquivos temporários do Python"
	@echo "  make stop    - Encerra a aplicação rodando na porta 8000"

install:
	pip install -r requirements.txt

run:
	$(UVICORN) $(APP) --reload

test:
	pytest

clean:
	@powershell -Command "Get-ChildItem -Recurse -Filter '__pycache__' | Remove-Item -Recurse -Force"

stop:
	@echo "A encerrar a aplicação na porta 8000..."
	@powershell -Command "Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess -ErrorAction SilentlyContinue | Stop-Process -Force"