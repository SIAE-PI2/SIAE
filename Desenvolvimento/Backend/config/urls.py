from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.contrib.auth import views as AuthViews

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/accounts/login/', permanent=False)),  # raiz → login
    path('accounts/', include('django.contrib.auth.urls')),                  # /accounts/login
    path('accounts/profile/', RedirectView.as_view(url='/produtos/', permanent=False)),
    path('', include(('estoque.urls', 'estoque'), namespace='estoque'))

    
]
