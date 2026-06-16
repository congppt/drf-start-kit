from django.core.validators import RegexValidator, validate_slug, validate_unicode_slug
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _


@deconstructible
class SlugValidator:
    def __call__(self, value):
        validate_slug(value)

    def __eq__(self, other):
        return isinstance(other, SlugValidator)


@deconstructible
class UnicodeSlugValidator:
    def __call__(self, value):
        validate_unicode_slug(value)

    def __eq__(self, other):
        return isinstance(other, UnicodeSlugValidator)


@deconstructible
class PhoneNumberValidator(RegexValidator):
    message = _("Enter a valid phone number in E.164 format, for example +84901234567.")
    regex = r"^\+[1-9]\d{1,14}$"


@deconstructible
class HexColorValidator(RegexValidator):
    message = _("Enter a valid hex color, for example #fff or #1a2b3c.")
    regex = r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$"
