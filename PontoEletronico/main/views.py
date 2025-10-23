from django.shortcuts import render
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from rest_framework.response import Response

from .models import Funcionario, RegistroPonto
from django.utils import timezone
from rest_framework import generics
from .serializers import PontoHistoricoSerializer
from django.db.models import Q
from datetime import datetime, timedelta


# Create your views here.

def historico(request):
    return render(request, "ponto/historico.html")


def registro(request):
    return render(request, 'ponto/index.html')


def main(request):
    return render(request, 'home/index.html')


@csrf_exempt
def login_api(request):
    if request.method == 'POST':
        try:
            # 1. Carrega o JSON
            data = json.loads(request.body)
            username = data.get('usuario')  # Corresponde ao campo 'usuario' do JS
            password = data.get('senha')
        except json.JSONDecodeError:
            return JsonResponse({'detail': 'Dados JSON inválidos.'}, status=400)

        # 2. Autentica o usuário usando o sistema nativo do Django (User Model)
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Login bem-sucedido
            login(request, user)  # Inicia a sessão

            try:
                # Tenta obter o perfil Funcionario
                funcionario = Funcionario.objects.get(user=user)
            except Funcionario.DoesNotExist:
                # Se for um User sem perfil Funcionario (ex: apenas um Admin)
                funcionario = None

            # 3. Retorna os dados em JSON
            return JsonResponse({
                'usuario': user.username,
                'nome': user.get_full_name() or user.username,
                'id': user.pk,
                # Exemplo de como retornar o perfil, se necessário
                'perfil_tipo': 'funcionario' if funcionario else 'admin',
            })
        else:
            # Falha na autenticação
            return JsonResponse({'detail': 'Usuário ou senha incorretos.'}, status=401)

    return JsonResponse({'detail': 'Método não permitido.'}, status=405)


@csrf_exempt
def ultimo_ponto_api(request):
    """
    Retorna o último registro de ponto do funcionário para determinar o próximo tipo
    """
    if request.method == 'GET':
        try:
            funcionario_id = request.GET.get('funcionario_id')

            if not funcionario_id:
                return JsonResponse({'detail': 'ID do funcionário não fornecido.'}, status=400)

            # Buscar o funcionário
            try:
                funcionario = Funcionario.objects.get(user__pk=funcionario_id)
            except Funcionario.DoesNotExist:
                return JsonResponse({'detail': 'Funcionário não encontrado.'}, status=404)

            # Buscar o último registro de ponto do funcionário
            ultimo_registro = RegistroPonto.objects.filter(
                funcionario=funcionario
            ).order_by('-timestamp').first()

            # Determinar o próximo tipo
            if ultimo_registro:
                # Se o último foi entrada, próximo é saída (vermelho)
                # Se o último foi saída, próximo é entrada (verde)
                proximo_tipo = 'S' if ultimo_registro.tipo == 'E' else 'E'
                ultimo_tipo = ultimo_registro.tipo
                ultimo_timestamp = ultimo_registro.timestamp.strftime('%d/%m/%Y %H:%M')
            else:
                # Primeiro registro do dia - sempre entrada (verde)
                proximo_tipo = 'E'
                ultimo_tipo = None
                ultimo_timestamp = None

            return JsonResponse({
                'proximo_tipo': proximo_tipo,
                'proximo_tipo_display': 'Saída' if proximo_tipo == 'S' else 'Entrada',
                'ultimo_tipo': ultimo_tipo,
                'ultimo_timestamp': ultimo_timestamp,
                'cor_botao': 'vermelho' if proximo_tipo == 'S' else 'verde'
            })

        except Exception as e:
            print(f"Erro ao buscar último ponto: {e}")
            return JsonResponse({'detail': 'Erro interno do servidor.'}, status=500)

    return JsonResponse({'detail': 'Método não permitido.'}, status=405)


@csrf_exempt
def registro_ponto_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            funcionario_id = data.get('funcionario_id')
            timestamp_frontend = data.get('timestamp')

            try:
                funcionario = Funcionario.objects.get(user__pk=funcionario_id)
            except Funcionario.DoesNotExist:
                return JsonResponse({'detail': 'Funcionário não encontrado.'}, status=404)

            # Lógica do tipo automático
            ultimo_registro = RegistroPonto.objects.filter(
                funcionario=funcionario
            ).order_by('-timestamp').first()

            if ultimo_registro:
                tipo = 'S' if ultimo_registro.tipo == 'E' else 'E'
            else:
                tipo = 'E'

            # 🆕 CORREÇÃO DO FUSO HORÁRIO
            from django.utils import timezone
            from datetime import datetime
            import pytz

            if timestamp_frontend:
                try:
                    # Converte o ISO string para datetime (em UTC)
                    timestamp_str = timestamp_frontend.replace('Z', '+00:00')
                    user_timestamp_utc = datetime.fromisoformat(timestamp_str)

                    # 🆕 CONVERTE PARA O FUSO HORÁRIO LOCAL (Manaus)
                    timezone_local = pytz.timezone('America/Manaus')
                    user_timestamp_local = user_timestamp_utc.astimezone(timezone_local)

                    timestamp_final = user_timestamp_local
                    fonte = 'frontend'
                    print(f"✅ Timestamp convertido: UTC {user_timestamp_utc} -> Manaus {user_timestamp_local}")

                except Exception as e:
                    print(f"Erro ao converter timestamp frontend: {e}")
                    timestamp_final = timezone.now()
                    fonte = 'servidor (fallback)'
            else:
                timestamp_final = timezone.now()
                fonte = 'servidor'

            # Cria o registro
            registro = RegistroPonto.objects.create(
                funcionario=funcionario,
                tipo=tipo,
                timestamp=timestamp_final
            )

            proximo_tipo = 'S' if tipo == 'E' else 'E'

            return JsonResponse({
                'detail': 'Ponto registrado com sucesso.',
                'tipo_registrado': registro.get_tipo_display(),
                'tipo_registrado_codigo': tipo,
                'proximo_tipo': proximo_tipo,
                'proximo_tipo_display': 'Saída' if proximo_tipo == 'S' else 'Entrada',
                'timestamp_formatado': registro.timestamp.strftime('%H:%M:%S'),
                'data_formatada': registro.timestamp.strftime('%d/%m/%Y'),
                'registro_id': registro.pk,
                'fonte_timestamp': fonte
            }, status=201)

        except Exception as e:
            print(f"Erro ao salvar ponto: {e}")
            return JsonResponse({'detail': 'Erro interno do servidor.'}, status=500)


@csrf_exempt
def logout_api(request):
    """
    Desloga o usuário do sistema de sessão do Django.
    """
    logout(request)
    return JsonResponse({'detail': 'Desconectado com sucesso.'})


class HistoricoPontoAPIView(generics.ListAPIView):
    serializer_class = PontoHistoricoSerializer

    def get_queryset(self):
        queryset = RegistroPonto.objects.all()

        # Debug: log dos parâmetros recebidos
        print("Parâmetros recebidos:", self.request.query_params)

        funcionario_id = self.request.query_params.get('funcionario_id')
        data_inicio_str = self.request.query_params.get('data_inicio')
        data_fim_str = self.request.query_params.get('data_fim')
        tipo = self.request.query_params.get('tipo')

        # Filtro por funcionário
        if funcionario_id:
            try:
                queryset = queryset.filter(funcionario__user__id=funcionario_id)
                print(f"Filtrando por funcionário ID: {funcionario_id}")
                print(f"Registros encontrados: {queryset.count()}")
            except ValueError:
                pass

        # Filtro por data início
        if data_inicio_str:
            try:
                data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
                queryset = queryset.filter(timestamp__date__gte=data_inicio)
                print(f"Filtrando a partir de: {data_inicio}")
            except ValueError:
                pass

        # Filtro por data fim
        if data_fim_str:
            try:
                data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date()
                queryset = queryset.filter(timestamp__date__lte=data_fim)
                print(f"Filtrando até: {data_fim}")
            except ValueError:
                pass

        # Filtro por tipo
        if tipo:
            tipo_map = {'entrada': 'E', 'saida': 'S'}
            tipo_db = tipo_map.get(tipo.lower())
            if tipo_db:
                queryset = queryset.filter(tipo=tipo_db)
                print(f"Filtrando por tipo: {tipo_db}")

        # Ordenar por data/hora (mais recente primeiro)
        queryset = queryset.order_by('-timestamp')

        print(f"✅ Total de registros no queryset: {queryset.count()}")

        return queryset

    def paginate_queryset(self, queryset):
        return None

    def get_paginated_response(self, data):
        return Response(data)