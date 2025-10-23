import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

class SpecialCharacterValidator:
    """
    Validador que verifica se a senha contém pelo menos um caractere especial
    (não-alfanumérico).
    """
    def __init__(self, special_characters=r'[!@#$%^&*(),.?":{}|<>]'):
        # Você pode expandir ou simplificar esta lista de caracteres especiais
        self.special_characters = special_characters
        self.regex = re.compile(special_characters)

    def validate(self, password, user=None):
        if not self.regex.search(password):
            raise ValidationError(
                _("A senha deve conter pelo menos um caractere especial: %(special_characters)s"),
                code='password_no_special_character',
                params={'special_characters': self.special_characters},
            )

    def get_help_text(self):
        return _(
            "Sua senha deve conter pelo menos um caractere especial (ex: !@#$%^&*)."
        )