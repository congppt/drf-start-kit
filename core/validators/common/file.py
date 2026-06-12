from django.core.files import File
from django.core.validators import validate_image_file_extension, RegexValidator
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError


class ImageFileExtensionValidator:
    def __call__(self, value: File):
        validate_image_file_extension(value)


class ImageFileNameValidator(RegexValidator):
    message = _('Invalid file name')
    regex = r'^[^/\\?%*:|"<>\x00]+$'
    max_length = 255
    allowed_extensions = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp'}

    def __call__(self, value: str):
        if not isinstance(value, str) or len(value) > self.max_length:
            raise ValidationError(self.message, code=self.code, params={"value": value})

        super().__call__(value)

        if '.' not in value:
            raise ValidationError(self.message, code=self.code, params={"value": value})

        name, extension = value.rsplit('.', 1)
        if not name or extension.lower() not in self.allowed_extensions:
            raise ValidationError(self.message, code=self.code, params={"value": value})