# Flask

## App factory em vez de app global

```python
# Não recomendado para projetos que crescem — app é um global mutável
from flask import Flask
app = Flask(__name__)

# Recomendado — app factory, facilita testes com configs diferentes
def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)
    if config:
        app.config.update(config)
    from .rotas import bp_produtos
    app.register_blueprint(bp_produtos)
    return app
```

## Blueprints para organizar rotas

```python
from flask import Blueprint, jsonify, request

bp_produtos = Blueprint("produtos", __name__, url_prefix="/produtos")

@bp_produtos.route("/", methods=["POST"])
def cria_produto():
    dados = request.get_json()
    if not dados or "nome" not in dados:
        return jsonify({"erro": "nome é obrigatório"}), 400
    produto = salva(dados)
    return jsonify(produto), 201
```

Um blueprint por área do domínio (produtos, vendas, usuários) em vez de todas as
rotas num único arquivo `app.py` — escala melhor conforme o projeto cresce.

## Validação de entrada: não confie em `request.get_json()` cru

```python
# Frágil — KeyError se campo faltar, sem validação de tipo
dados = request.get_json()
nome = dados["nome"]
quantidade = int(dados["quantidade"])  # ValueError não tratado se vier string inválida

# Recomendado — validar com Pydantic (ou Marshmallow) antes de usar
from pydantic import BaseModel, ValidationError

class ProdutoIn(BaseModel):
    nome: str
    quantidade: int

@bp_produtos.route("/", methods=["POST"])
def cria_produto():
    try:
        produto = ProdutoIn.model_validate(request.get_json())
    except ValidationError as e:
        return jsonify({"erro": e.errors()}), 400
    ...
```

Flask não valida payload automaticamente (diferente de FastAPI) — isso é
responsabilidade do código da rota. Ver [pydantic.md](pydantic.md).

## Contexto de aplicação e de requisição

```python
from flask import current_app, g

@bp_produtos.route("/")
def lista():
    db = g.get("db") or conecta_banco(current_app.config["DATABASE_URL"])
    ...
```

`g` guarda estado por-requisição (ex.: conexão de banco aberta uma vez por
request); não usar variáveis globais de módulo para isso — não é thread-safe
entre requisições concorrentes.

## Erro comum: lógica de negócio dentro da view

```python
# Errado — view faz validação, regra de negócio e acesso a dados tudo junto
@bp_produtos.route("/<int:id>/retirar", methods=["POST"])
def retirar(id):
    produto = db.session.get(Produto, id)
    qtd = request.json["quantidade"]
    if produto.quantidade < qtd:
        return jsonify({"erro": "insuficiente"}), 409
    produto.quantidade -= qtd
    db.session.commit()
    return jsonify(produto.to_dict())

# Melhor — view só traduz HTTP <-> domínio; regra vive numa função/serviço testável
@bp_produtos.route("/<int:id>/retirar", methods=["POST"])
def retirar(id):
    try:
        produto = servico_estoque.retirar(id, request.json["quantidade"])
    except EstoqueInsuficienteError as e:
        return jsonify({"erro": str(e)}), 409
    return jsonify(produto.to_dict())
```

Separar assim permite testar `servico_estoque.retirar` sem precisar de um
cliente HTTP de teste.

## Checklist ao revisar código Flask

- [ ] Rotas organizadas em blueprints, não tudo num arquivo.
- [ ] Payload de entrada validado (Pydantic/Marshmallow), não acessado direto via `request.json["campo"]`.
- [ ] Regra de negócio vive fora da view, em função/serviço testável isoladamente.
- [ ] Nenhum estado global mutável compartilhado entre requisições (usar `g` ou passar explícito).
