from io import BytesIO

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.forms import AuthenticationForm
from django.urls import reverse
from django.http import HttpResponse
from django.db import models
from django.db.models import Q, Sum
from django.utils import timezone
import pandas as pd

from .models import Produto, Retirada, Solicitacao, MovimentacaoEstoque
from .forms import ProdutoForm, RetiradaForm, SolicitacaoForm, MovimentacaoEstoqueForm


# =========================
# AUTENTICAÇÃO
# =========================
def login_view(request):
    """Login usando AuthenticationForm e preservando o ?next=."""
    if request.user.is_authenticated:
        return redirect('estoque:dashboard')

    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = (
                request.POST.get('next')
                or request.GET.get('next')
                or reverse('estoque:dashboard')
            )
            return redirect(next_url)
        else:
            messages.error(request, 'Usuário ou senha inválidos.')

    return render(request, 'registration/login.html', {
        'form': form,
        'next': request.GET.get('next', '')
    })


def logout_view(request):
    logout(request)
    return redirect('login')  # usa o name 'login' (auth padrão) ou sua rota


# =========================
# DASHBOARD
# =========================
@login_required
def dashboard(request):
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    tipo = request.GET.get('tipo')

    filtros = {}
    movimentos = MovimentacaoEstoque.objects.all()

    if data_inicio:
        movimentos = movimentos.filter(data__date__gte=data_inicio)
        filtros['data_inicio'] = data_inicio

    if data_fim:
        movimentos = movimentos.filter(data__date__lte=data_fim)
        filtros['data_fim'] = data_fim

    if tipo:
        movimentos = movimentos.filter(tipo=tipo)
        filtros['tipo'] = tipo

    entradas = movimentos.filter(tipo='E').aggregate(total=Sum('quantidade'))['total'] or 0
    saidas = movimentos.filter(tipo='S').aggregate(total=Sum('quantidade'))['total'] or 0

    produtos_movimentados = (
        movimentos.values('produto__nome')
        .annotate(total=Sum('quantidade'))
        .order_by('-total')[:10]
    )

    produtos_riticos = Produto.objects.filter(
        models.Q(estoque_fisico__lte=models.F('estoque_minimo')) &
        models.Q(estoque_fisico__isnull=False) &
        models.Q(estoque_minimo__isnull=False)
    )

    return render(request, 'registration/dashboard.html', {
        'entradas': entradas,
        'saidas': saidas,
        'produtos_movimentados': produtos_movimentados,
        'produtos_criticos': produtos_riticos,
        'pendentes': 0,
        'filtros': filtros,
    })


# =========================
# PRODUTOS
# =========================
@user_passes_test(lambda u: u.is_superuser)
def cadastrar_produto(request):
    if request.method == 'POST':
        form = ProdutoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Produto cadastrado com sucesso.')
            return redirect('estoque:dashboard')
    else:
        form = ProdutoForm()
    return render(request, 'registration/cadastro.html', {'form': form})


@login_required
def lista_produtos(request):
    produtos = Produto.objects.all().order_by('nome')
    return render(request, 'registration/listar_produtos.html', {'produtos': produtos})


# =========================
# MOVIMENTAÇÃO
# =========================
@user_passes_test(lambda u: u.is_superuser)
def registrar_movimentacao(request):
    if request.method == 'POST':
        form = MovimentacaoEstoqueForm(request.POST)
        if form.is_valid():
            movimentacao = form.save(commit=False)
            produto = movimentacao.produto

            if movimentacao.tipo == 'E':
                produto.estoque_fisico += movimentacao.quantidade
            else:  # 'S'
                if movimentacao.quantidade > (produto.estoque_fisico or 0):
                    messages.error(request, 'Estoque insuficiente.')
                    return redirect('estoque:registrar_movimentacao')
                produto.estoque_fisico -= movimentacao.quantidade

            produto.save()
            movimentacao.save()
            messages.success(request, 'Movimentação registrada com sucesso.')
            return redirect('estoque:dashboard')
    else:
        form = MovimentacaoEstoqueForm()

    return render(request, 'registration/movimentar_estoque.html', {'form': form})


# =========================
# SOLICITAÇÕES / RETIRADAS
# =========================
@login_required
def solicitar_retirada(request):
    if request.method == 'POST':
        produto_id = request.POST.get('produto_id')
        quantidade = int(request.POST.get('quantidade'))
        observacao = request.POST.get('observacao', '')

        produto = get_object_or_404(Produto, id=produto_id)

        Retirada.objects.create(
            produto=produto,
            quantidade=quantidade,
            solicitante=request.user,
            data_retirada=timezone.now(),
            status='PENDENTE',
            observacao=observacao
        )

        messages.success(request, 'Solicitação registrada com sucesso.')
        return redirect('estoque:dashboard')

    produtos = Produto.objects.all().order_by('nome')
    return render(request, 'registration/solicitar_retirada.html', {'produtos': produtos})


@staff_member_required
def listar_retiradas(request):
    retiradas = Retirada.objects.all().order_by('-data_retirada')
    return render(request, 'registration/listar_retiradas.html', {'retiradas': retiradas})


@staff_member_required
def aprovar_retirada(request, pk):
    retirada = get_object_or_404(Retirada, pk=pk)

    if retirada.status != 'PENDENTE':
        messages.warning(request, 'Retirada já foi processada.')
        return redirect('estoque:listar_retiradas')

    produto = retirada.produto
    quantidade = retirada.quantidade

    if (produto.estoque_fisico or 0) < quantidade:
        messages.error(request, 'Estoque insuficiente para aprovação.')
        return redirect('estoque:listar_retiradas')

    # 1) Atualiza estoque
    produto.estoque_fisico -= quantidade
    produto.save()

    # 2) Registra movimentação de saída
    MovimentacaoEstoque.objects.create(
        produto=produto,
        tipo='S',
        quantidade=quantidade
    )

    # 3) Atualiza status
    retirada.status = 'APROVADA'
    retirada.save()

    messages.success(request, 'Retirada aprovada com sucesso.')
    return redirect('estoque:listar_retiradas')


@staff_member_required
def negar_retirada(request, retirada_id=None, pk=None):
    """Aceita tanto retirada_id quanto pk (para compatibilizar URLs)."""
    rid = pk or retirada_id
    retirada = get_object_or_404(Retirada, id=rid)
    if retirada.status == 'PENDENTE':
        retirada.status = 'RECUSADA'
        retirada.save()
        messages.info(request, 'Retirada recusada.')
    return redirect('estoque:listar_retiradas')


# =========================
# EXPORTAÇÃO
# =========================
@user_passes_test(lambda u: u.is_superuser)
def exportar_excel(request):
    produtos = Produto.objects.all().order_by('nome')
    dados = [{
        'Produto': p.nome,
        'Estoque': p.estoque_fisico,
        'Preço Unitário': float(p.preco_unitario) if p.preco_unitario is not None else None
    } for p in produtos]

    df = pd.DataFrame(dados)

    # escreve em memória (xlsx)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)

    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="estoque.xlsx"'
    return response


@user_passes_test(lambda u: u.is_superuser)
def exportar_solicitacoes_excel(request):
    solicitacoes = Solicitacao.objects.select_related('produto', 'usuario').all().order_by('-data_solicitacao')

    dados = [{
        'Código OS': s.codigo_os,
        'Produto': s.produto.nome if s.produto else '',
        'Usuário': s.usuario.username if s.usuario else '',
        'Quantidade': s.quantidade,
        'Status': s.status,
        'Data da Solicitação': s.data_solicitacao.strftime('%d/%m/%Y %H:%M') if s.data_solicitacao else ''
    } for s in solicitacoes]

    df = pd.DataFrame(dados)

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)

    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="solicitacoes.xlsx"'
    return response


# =========================
# IMPORTAÇÃO DE PLANILHA (utilitário)
# =========================
@user_passes_test(lambda u: u.is_superuser)
def importar_planilha(request):
    """
    Lê 'controle epi.xlsx' do diretório atual do projeto e cria produtos válidos.
    Ao final, redireciona para o dashboard com mensagens de status.
    """
    try:
        df = pd.read_excel('controle epi.xlsx')
    except Exception as e:
        messages.error(request, f'Não foi possível ler a planilha: {e}')
        return redirect('estoque:dashboard')

    df.columns = df.columns.str.strip()

    produtos_criados = 0
    for _, row in df.iterrows():
        nome = str(row.get('Nome', '')).strip()
        if nome.lower() == 'nan' or nome == '' or pd.isna(nome):
            continue

        estoque_fisico = row.get('Estoque')
        if pd.isna(estoque_fisico):
            continue

        try:
            estoque_fisico = int(estoque_fisico)
            estoque_minimo = int(row.get('Estoque Minimo', 0) or 0)
            preco_unitario = float(row.get('Preço Unitario', 0.0) or 0.0)

            Produto.objects.create(
                nome=nome,
                estoque_fisico=estoque_fisico,
                estoque_minimo=estoque_minimo,
                preco_unitario=preco_unitario
            )
            produtos_criados += 1
        except Exception as e:
            # Log simples; se quiser, acumula e mostra no messages depois
            print(f"Erro ao importar linha: {row.to_dict()} | Erro: {e}")

    messages.success(request, f'{produtos_criados} produtos importados com sucesso!')
    return redirect('estoque:dashboard')
