from django.db import models
from django.db.models.enums import ChoicesType


class TextChoiceField(models.CharField):
    """
    CharField that coerces DB/raw values into members of a ``models.TextChoices`` enum.

    Pass the enum class as ``choices`` (not ``Enum.choices``)::

        nationality = EnumCharField(max_length=100, choices=Country, null=True)
    """

    def __init__(self, *args, choices=None, **kwargs):
        self.enum_class = self._resolve_enum_class(choices)
        super().__init__(*args, choices=choices, **kwargs)

    @staticmethod
    def _resolve_enum_class(choices):
        if isinstance(choices, ChoicesType) and issubclass(choices, models.Choices):
            return choices
        return None

    def from_db_value(self, value, expression, connection):
        return self.to_python(value)

    def to_python(self, value):
        value = super().to_python(value)
        return self._to_enum(value)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if self.enum_class is not None:
            kwargs["choices"] = self.enum_class
        return name, path, args, kwargs

    def _to_enum(self, value):
        if value is None or self.enum_class is None:
            return value
        if isinstance(value, self.enum_class):
            return value
        try:
            return self.enum_class(value)
        except ValueError:
            return value
