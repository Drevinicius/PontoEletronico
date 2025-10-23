# ponto/utils.py
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from django.utils import timezone
from datetime import datetime, timedelta
from .models import RegistroPonto


def gerar_relatorio_ponto_pdf(funcionario, data_inicio, data_fim):
    """
    Gera relatório de pontos em PDF para um funcionário específico
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        leftMargin=15 * mm,
        rightMargin=15 * mm
    )
    elements = []

    # Estilos
    styles = getSampleStyleSheet()

    estilo_cabecalho = ParagraphStyle(
        'Cabecalho',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=12,
        textColor=colors.darkblue
    )

    estilo_dados = ParagraphStyle(
        'Dados',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6
    )

    # Cabeçalho
    data_fechamento = timezone.now().strftime('%d/%m/%Y %H:%M')
    cabecalho_texto = f"""
    <b>RELATÓRIO DE PONTOS</b><br/>
    <b>Funcionário:</b> {funcionario.user.get_full_name() or funcionario.user.username}<br/>
    <b>CPF:</b> {funcionario.cpf or 'Não informado'}<br/>
    <b>Cargo:</b> {funcionario.cargo or 'Não informado'}<br/>
    <b>Período:</b> {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}<br/>
    <b>Data de Fechamento:</b> {data_fechamento}
    """

    elements.append(Paragraph(cabecalho_texto, estilo_cabecalho))
    elements.append(Spacer(1, 15 * mm))

    # Buscar registros do período
    registros = RegistroPonto.objects.filter(
        funcionario=funcionario,
        timestamp__date__gte=data_inicio,
        timestamp__date__lte=data_fim
    ).order_by('timestamp')

    # Agrupar registros por dia
    registros_por_dia = {}
    for registro in registros:
        data = registro.timestamp.date()
        if data not in registros_por_dia:
            registros_por_dia[data] = []
        registros_por_dia[data].append(registro)

    # Se não houver registros
    if not registros_por_dia:
        elements.append(Paragraph("<b>Nenhum registro de ponto encontrado no período.</b>", estilo_dados))
        doc.build(elements)
        buffer.seek(0)
        return buffer

    # Tabela de registros
    dados_tabela = []

    # Cabeçalho da tabela
    cabecalho = ['Data', 'Entrada 1', 'Saída 1', 'Entrada 2', 'Saída 2', 'Entrada 3', 'Saída 3', 'Entrada 4', 'Saída 4',
                 'Total Horas', 'Horas Extras']
    dados_tabela.append(cabecalho)

    # Preencher dados
    for data, registros_dia in sorted(registros_por_dia.items()):
        linha = [data.strftime('%d/%m/%Y')]

        # Inicializar horários
        horarios = ['-', '-', '-', '-', '-', '-', '-', '-']

        # Preencher horários na ordem correta (entrada/saída)
        entrada_count = 0
        saida_count = 0

        for registro in registros_dia:
            if registro.tipo == 'E' and entrada_count < 4:
                horarios[entrada_count * 2] = registro.timestamp.strftime('%H:%M')
                entrada_count += 1
            elif registro.tipo == 'S' and saida_count < 4:
                horarios[saida_count * 2 + 1] = registro.timestamp.strftime('%H:%M')
                saida_count += 1

        linha.extend(horarios)

        # Calcular totais
        total_horas = calcular_total_horas(registros_dia)
        horas_extras = calcular_horas_extras(total_horas)

        linha.append(total_horas)
        linha.append(horas_extras)

        dados_tabela.append(linha)

    # Criar tabela
    tabela = Table(dados_tabela, repeatRows=1)
    estilo_tabela = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')])
    ])
    tabela.setStyle(estilo_tabela)

    elements.append(tabela)

    # Rodapé com totais
    elements.append(Spacer(1, 10 * mm))
    total_registros = registros.count()
    elements.append(Paragraph(f"<b>Total de registros no período:</b> {total_registros}", estilo_dados))

    # Gerar PDF
    doc.build(elements)

    buffer.seek(0)
    return buffer


def calcular_total_horas(registros_dia):
    """
    Calcula o total de horas trabalhadas no dia de forma mais precisa
    """
    if len(registros_dia) < 2:
        return "0:00"

    # Ordenar por timestamp
    registros_ordenados = sorted(registros_dia, key=lambda x: x.timestamp)

    total_segundos = 0
    i = 0

    while i < len(registros_ordenados) - 1:
        # Procura por um par entrada-saída
        if registros_ordenados[i].tipo == 'E' and registros_ordenados[i + 1].tipo == 'S':
            entrada = registros_ordenados[i].timestamp
            saida = registros_ordenados[i + 1].timestamp

            # Calcular diferença em segundos
            diferenca = saida - entrada
            total_segundos += diferenca.total_seconds()

            i += 2  # Pular para o próximo par
        else:
            i += 1  # Avançar se não for um par válido

    horas = int(total_segundos // 3600)
    minutos = int((total_segundos % 3600) // 60)

    return f"{horas}:{minutos:02d}"


def calcular_horas_extras(total_horas):
    """
    Calcula horas extras (considerando jornada de 8 horas)
    """
    try:
        if total_horas == "0:00":
            return "0:00"

        horas, minutos = map(int, total_horas.split(':'))
        total_minutos = horas * 60 + minutos

        jornada_normal = 8 * 60  # 8 horas em minutos

        if total_minutos > jornada_normal:
            extras_minutos = total_minutos - jornada_normal
            extras_horas = extras_minutos // 60
            extras_minutos = extras_minutos % 60
            return f"+{extras_horas}:{extras_minutos:02d}"
        else:
            deficit_minutos = jornada_normal - total_minutos
            deficit_horas = deficit_minutos // 60
            deficit_minutos = deficit_minutos % 60
            return f"-{deficit_horas}:{deficit_minutos:02d}" if deficit_minutos > 0 else "0:00"
    except:
        return "0:00"