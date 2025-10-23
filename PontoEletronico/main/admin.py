from django.contrib import admin
from .models import Funcionario, RegistroPonto
from django.http import HttpResponse
from django.utils import timezone
from datetime import timedelta
from .utils import gerar_relatorio_ponto_pdf


class AdminFuncionario(admin.ModelAdmin):
    list_display = ("id", "nome_completo", 'cpf', 'telefone', 'cargo', 'data_admissao')
    list_display_links = ("id", "nome_completo")
    list_filter = ['cargo', 'data_admissao']
    search_fields = ['user__first_name', 'user__last_name', 'user__username', 'cpf']
    fieldsets = (
        ('Dados de Usuário', {
            'fields': ('user',)
        }),
        ('Informações Pessoais', {
            'fields': ('cpf', 'telefone', 'data_nascimento', 'endereco')
        }),
        ('Informações Profissionais', {
            'fields': ('cargo', 'data_admissao')
        }),
    )

    # 🟢 ACTION PARA GERAR RELATÓRIO EM PDF
    actions = ['gerar_relatorio_mensal_pdf']

    def nome_completo(self, obj):
        return obj.user.get_full_name() or obj.user.username

    nome_completo.short_description = 'Nome'
    nome_completo.admin_order_field = 'user__first_name'

    def gerar_relatorio_mensal_pdf(self, request, queryset):
        """
        Gera relatório mensal em PDF para funcionários selecionados
        """
        if len(queryset) != 1:
            self.message_user(request, "❌ Selecione apenas UM funcionário para gerar o relatório.", level='ERROR')
            return

        funcionario = queryset[0]

        # Definir período do mês atual
        hoje = timezone.now().date()
        primeiro_dia_mes = hoje.replace(day=1)
        ultimo_dia_mes = (primeiro_dia_mes + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        try:
            # Gerar PDF
            buffer = gerar_relatorio_ponto_pdf(funcionario, primeiro_dia_mes, ultimo_dia_mes)

            # Configurar resposta
            nome_arquivo = f"relatorio_ponto_{funcionario.user.username}_{hoje.strftime('%Y_%m')}.pdf"

            response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{nome_arquivo}"'

            self.message_user(request, f"✅ Relatório gerado com sucesso para {self.nome_completo(funcionario)}")
            return response

        except Exception as e:
            self.message_user(request, f"❌ Erro ao gerar relatório: {str(e)}", level='ERROR')

    gerar_relatorio_mensal_pdf.short_description = "📄 Gerar relatório mensal (PDF)"


# 🟢 REGISTRE CADA MODELO APENAS UMA VEZ
admin.site.register(Funcionario, AdminFuncionario)


@admin.register(RegistroPonto)
class AdminRegistroPonto(admin.ModelAdmin):
    list_display = ('id', 'funcionario_nome', 'tipo', 'timestamp_formatado')
    list_filter = ('tipo', 'timestamp')
    search_fields = ('funcionario__user__first_name', 'funcionario__user__last_name')

    def funcionario_nome(self, obj):
        return obj.funcionario.user.get_full_name() or obj.funcionario.user.username

    funcionario_nome.short_description = 'Funcionário'
    funcionario_nome.admin_order_field = 'funcionario__user__first_name'

    def timestamp_formatado(self, obj):
        return obj.timestamp.strftime('%d/%m/%Y %H:%M')

    timestamp_formatado.short_description = 'Data/Hora'
    timestamp_formatado.admin_order_field = 'timestamp'