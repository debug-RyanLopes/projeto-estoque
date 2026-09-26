# Django

## Models: onde a regra de negócio simples vive

```python
from django.db import models

class Produto(models.Model):
    nome = models.CharField(max_length=200)
    quantidade = models.PositiveIntegerField(default=0)
    preco = models.DecimalField(max_digits=10, decimal_places=2)

    def retirar(self, qtd: int) -> None:
        if qtd > self.quantidade:
            raise EstoqueInsuficienteError(self.nome, self.quantidade, qtd)
        self.quantidade -= qtd
        self.save(update_fields=["quantidade"])
```

`update_fields` evita sobrescrever outros campos que podem ter mudado
concorrentemente — sempre preferir a especificar quando só um campo mudou.

## `DecimalField` para dinheiro, nunca `FloatField`

```python
# Errado — float acumula erro de arredondamento em somas de dinheiro
preco = models.FloatField()

# Certo
preco = models.DecimalField(max_digits=10, decimal_places=2)
```

## QuerySets são lazy — cuidado com N+1

```python
# Errado — 1 query para listar produtos + 1 query por produto para pegar a categoria
produtos = Produto.objects.all()
for p in produtos:
    print(p.categoria.nome)  # dispara uma query por iteração

# Certo — select_related faz JOIN numa única query (FK/OneToOne)
produtos = Produto.objects.select_related("categoria")

# prefetch_related para ManyToMany / reverse FK (queries separadas, mas só 2 no total)
produtos = Produto.objects.prefetch_related("tags")
```

Esse é o erro de performance mais comum em código Django — sempre checar se um
loop sobre um QuerySet acessa uma relação (`.campo_relacionado.algo`) sem
`select_related`/`prefetch_related` correspondente.

## Forms/Serializers para validação, não direto no view

```python
# Django puro
from django import forms

class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = ["nome", "quantidade", "preco"]

def cria_produto(request):
    form = ProdutoForm(request.POST)
    if form.is_valid():
        form.save()
        return redirect("lista_produtos")
    return render(request, "produtos/form.html", {"form": form})
```

Para APIs, o equivalente é Django REST Framework `Serializer`/`ModelSerializer` —
mesma ideia: nunca confiar em `request.POST`/`request.data` cru sem validação.

## Migrations: nunca editar uma migration já aplicada em produção

```bash
python manage.py makemigrations
python manage.py migrate
```

Se uma migration já foi aplicada em qualquer ambiente compartilhado (staging,
produção), criar uma **nova** migration para corrigir, nunca editar o arquivo
já existente — editar quebra o histórico para quem já aplicou.

## Views baseadas em classe vs função

```python
# CBV — bom para CRUD padrão, reaproveita comportamento genérico
from django.views.generic import ListView

class ListaProdutos(ListView):
    model = Produto
    paginate_by = 20

# FBV — bom quando a lógica foge do padrão CRUD, mais explícito para casos únicos
def retirar_estoque(request, produto_id):
    ...
```

Não force CBV para uma view com lógica de negócio complexa e não-padrão só por
convenção — function-based view explícita costuma ser mais legível nesse caso.

## Checklist ao revisar código Django

- [ ] Dinheiro em `DecimalField`, nunca `FloatField`.
- [ ] Loop sobre QuerySet que acessa relação usa `select_related`/`prefetch_related`.
- [ ] Entrada de usuário (POST/JSON) validada via Form/Serializer, nunca lida direto do request.
- [ ] `save()` com `update_fields` quando só parte dos campos mudou.
- [ ] Nenhuma migration já aplicada em produção foi editada — sempre uma nova migration.
