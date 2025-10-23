from django.urls import path
from .views import main, registro, login_api, registro_ponto_api, logout_api, historico, HistoricoPontoAPIView, ultimo_ponto_api  # 🟢 Adicione a nova view

app_name = 'main'

urlpatterns =[
    path('', main, name='inicio'),
    path('registro/', registro, name='registro'),
    path('historico/', historico, name='historico'),
    path('api/login/', login_api, name='login_api'),
    path('api/ultimo-ponto/', ultimo_ponto_api, name='ultimo_ponto_api'),  # 🟢 Nova URL
    path('api/registro-ponto/', registro_ponto_api, name='registro_ponto_api'),
    path('api/logout/', logout_api, name='logout_api'),
    path("api/historico-ponto/", HistoricoPontoAPIView.as_view(), name="historico-ponto-api"),
]