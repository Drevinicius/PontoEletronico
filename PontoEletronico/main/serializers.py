# CORREÇÃO NO serializers.py
from rest_framework import serializers
from .models import RegistroPonto, Funcionario
from django.utils import timezone

class PontoHistoricoSerializer(serializers.ModelSerializer):
    funcionarioId = serializers.IntegerField(source='funcionario.user.id', read_only=True)
    funcionarioNome = serializers.CharField(source='funcionario.user.get_full_name', read_only=True)  # Corrigido
    tipo = serializers.SerializerMethodField()
    data = serializers.SerializerMethodField()
    hora = serializers.SerializerMethodField()

    class Meta:
        model = RegistroPonto
        fields = ('id', 'funcionarioId', 'funcionarioNome', 'tipo', 'timestamp', 'data', 'hora')

    def get_tipo(self, obj):
        # Retorna 'entrada' ou 'saida' em minúsculas
        return obj.get_tipo_display().lower()

    def get_data(self, obj):
        local_time = timezone.localtime(obj.timestamp)
        return local_time.strftime('%d/%m/%Y')

    def get_hora(self, obj):
        local_time = timezone.localtime(obj.timestamp)
        return local_time.strftime('%H:%M')

class FuncionarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Funcionario
        fields = ('id', 'user', 'cpf', 'telefone', 'endereco', 'cargo', 'data_admissao')