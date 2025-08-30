from django.contrib.auth.models import User
from django.db import models
import uuid

class Produto(models.Model):
    nome = models.CharField(max_length=100)
    estoque_fisico = models.IntegerField()
    estoque_minimo = models.IntegerField(default=0)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    def __str__(self):
        return self.nome

class Solicitacao(models.Model):
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('APROVADA', 'Aprovada'),
        ('NEGADA', 'Negada'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    quantidade = models.PositiveIntegerField()
    data_solicitacao = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDENTE')
    codigo_os = models.CharField(max_length=12, unique=True, default=uuid.uuid4)

    def __str__(self):
        return f"OS-{self.codigo_os} ({self.usuario.username})"

class Retirada(models.Model):
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('APROVADA', 'Aprovada'),
        ('RECUSADA', 'Recusada'),
    ]

    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    quantidade = models.PositiveIntegerField()
    solicitante = models.ForeignKey(User, on_delete=models.CASCADE)
    data_retirada = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDENTE')
    observacao = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'{self.solicitante.username} - {self.quantidade}x {self.produto.nome} - {self.status}'

class MovimentacaoEstoque(models.Model):
    TIPO_CHOICES = (
        ('E', 'Entrada'),
        ('S', 'Saída'),
    )
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=1, choices=TIPO_CHOICES)
    quantidade = models.PositiveIntegerField()
    data = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.get_tipo_display()} - {self.produto.nome} ({self.quantidade})'