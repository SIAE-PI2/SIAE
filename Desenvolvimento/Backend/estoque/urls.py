from django.contrib import admin
from django.urls import path
from estoque import views
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView


app_name = 'estoque'  # namespace

urlpatterns = [
    path('', views.dashboard, name='dashboard'),  # raiz do app → dashboard
    path('produtos/', views.lista_produtos, name='lista_produtos'),
    path('cadastrar/', views.cadastrar_produto, name='cadastrar_produto'),
    path('movimentar/', views.registrar_movimentacao, name='registrar_movimentacao'),

    path('retirada/solicitar/', views.solicitar_retirada, name='solicitar_retirada'),
    path('retiradas/', views.listar_retiradas, name='listar_retiradas'),
    path('retirada/aprovar/<int:pk>/', views.aprovar_retirada, name='aprovar_retirada'),
    path('retirada/negar/<int:retirada_id>/', views.negar_retirada, name='negar_retirada'),

    path('exportar/excel/', views.exportar_excel, name='exportar_excel'),
    path('exportar/solicitacoes/', views.exportar_solicitacoes_excel, name='exportar_solicitacoes'),
]
    
    # Dashboard
path('dashboard/', views.dashboard, name='dashboard'),

    # Produtos
path('produtos/', views.lista_produtos, name='lista_produtos'),
path('cadastrar/', views.cadastrar_produto, name='cadastrar'),
path('registrar_movimentacao/', views.registrar_movimentacao, name='registrar_movimentacao'),
path('exportar_solicitacoes/', views.exportar_solicitacoes_excel, name='exportar_solicitacoes'),
   
    # Solicitação e retirada
path('retirada/', views.solicitar_retirada, name='retirada'),
path('retiradas/', views.listar_retiradas, name='listar_retiradas'),
path('retirada/aprovar/<int:pk>/', views.aprovar_retirada, name='aprovar_retirada'),
path('retirada/negar/<int:pk>/', views.negar_retirada, name='negar_retirada'),
    
    # Exportações
path('exportar_solicitacoes/', views.exportar_solicitacoes_excel, name='exportar_solicitacoes'),
path('exportar_excel/', views.exportar_excel, name='exportar_excel'),       


