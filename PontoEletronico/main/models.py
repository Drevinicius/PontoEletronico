from django.core.validators import RegexValidator
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


# 1. Perfil de Funcionário (extensão do User nativo)
# Isso permite que usemos o sistema de login nativo (seguro)

class Funcionario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    cpf = models.CharField(
        max_length=14,
        unique=True,
        validators=[RegexValidator(regex=r'\d{3}\.\d{3}\.\d{3}-\d{2}$',
                                   message='CPF deve estar no formato: 000.000.000-00')],
        verbose_name='CPF',
        blank=True,
        null=True
    )

    telefone = models.CharField(
        max_length=15,
        validators=[RegexValidator(regex=r'^\(\d{2}\) \d{4,5}-\d{4}$',
                                 message='Telefone deve estar no formato: (00) 00000-0000')],
        blank=True,
        null=True
    )

    endereco = models.TextField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Endereço Completo'
    )

    data_nascimento = models.DateField(
        blank=True,
        null=True,
        verbose_name='Data de Nascimento'
    )

    # Campos de data de registro
    data_admissao = models.DateField(
        default=timezone.now,
        verbose_name='Data de Admissão'
    )

    cargo = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    def __str__(self):
        # Exibe o nome completo do usuário, se disponível, ou o username
        return self.user.get_full_name() or self.user.username

    class Meta:
        verbose_name = 'Funcionário'
        verbose_name_plural = 'Funcionários'


class RegistroPonto(models.Model):
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=timezone.now)


    # Campo para indicar o tipo de registro (ex: 'ENTRADA', 'SAÍDA')
    TIPO_PONTO = [
        ('E', 'Entrada'),
        ('S', 'Saída'),
        # Você pode adicionar mais, ex: ('I', 'Início Intervalo'), ('F', 'Fim Intervalo')
    ]
    tipo = models.CharField(max_length=7, choices=TIPO_PONTO)

    def __str__(self):
        return f"{self.funcionario.user.username} - {self.get_tipo_display()} - {self.timestamp.strftime('%d/%m/%Y %H:%M:%S')}"

    class Meta:
        # Define a ordem padrão dos registros de ponto (o mais recente primeiro)
        ordering = ['-timestamp']