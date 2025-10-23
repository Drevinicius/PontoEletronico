# ponto/forms.py
from django import forms

class RelatorioForm(forms.Form):
    data_inicio = forms.DateField(
        label='Data Início',
        widget=forms.SelectDateWidget(
            years=range(2020, 2031)
        )
    )
    data_fim = forms.DateField(
        label='Data Fim',
        widget=forms.SelectDateWidget(
            years=range(2020, 2031)
        )
    )