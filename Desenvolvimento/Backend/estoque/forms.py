from django import forms
from .models import Produto, Retirada
from .models import Solicitacao
from .models import MovimentacaoEstoque

class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = '__all__'

class RetiradaForm(forms.ModelForm):
    class Meta:
        model = Retirada
        fields = ['produto', 'quantidade', 'solicitante']

class SolicitacaoForm(forms.ModelForm):
    class Meta:
        model = Solicitacao
        fields = ['produto', 'quantidade']

class MovimentacaoEstoqueForm(forms.ModelForm):
    class Meta:
        model = MovimentacaoEstoque
        fields = ['produto', 'tipo', 'quantidade']
        
class MovimentacaoEstoqueForm(forms.ModelForm):
    class Meta:
        model = MovimentacaoEstoque
        fields = ['produto', 'tipo', 'quantidade']       