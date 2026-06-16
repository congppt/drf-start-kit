from django.conf import settings
from django.core.files import File
from django.core.validators import validate_image_file_extension, RegexValidator
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError


class _UnsetMaxSizeType:
    def __repr__(self):
        return 'UNSET_MAX_SIZE'


UNSET_MAX_SIZE = _UnsetMaxSizeType()


@deconstructible
class FileSizeValidator:
    message = _('The selected file is invalid.')
    min_message = _('The selected file is invalid.')
    max_message = _('The selected file is too large.')

    def __init__(self, min_size: int = 1, max_size: int | None = UNSET_MAX_SIZE):
        self.min_size = min_size
        self.max_size = max_size

    def _effective_max_size(self) -> int | None:
        if self.max_size is UNSET_MAX_SIZE:
            return settings.FILE_UPLOAD_MAX_MEMORY_SIZE
        return self.max_size

    def __call__(self, value: int):
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValidationError(_('The selected file is invalid.'), code='invalid')

        if value < self.min_size:
            raise ValidationError(
                self.min_message,
                code='min_value',
                params={'min_size': self.min_size, 'value': value},
            )

        max_size = self._effective_max_size()
        if max_size is not None and value > max_size:
            raise ValidationError(
                self.max_message,
                code='max_value',
                params={'max_size': max_size, 'value': value},
            )

    def deconstruct(self):
        kwargs = {}
        if self.min_size != 1:
            kwargs['min_size'] = self.min_size
        if self.max_size is not UNSET_MAX_SIZE:
            kwargs['max_size'] = self.max_size
        return (
            'core.validators.common.file.FileSizeValidator',
            [],
            kwargs,
        )

    def __eq__(self, other):
        return (
            isinstance(other, FileSizeValidator)
            and self.min_size == other.min_size
            and self.max_size == other.max_size
        )


@deconstructible
class ImageFileExtensionValidator:
    def __call__(self, value: File):
        validate_image_file_extension(value)

    def __eq__(self, other):
        return isinstance(other, ImageFileExtensionValidator)


class ImageFileNameValidator(RegexValidator):
    message = _('This image file is not supported. Please upload another image.')
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

    def __eq__(self, other):
        return (
            isinstance(other, ImageFileNameValidator)
            and super().__eq__(other)
            and self.allowed_extensions == other.allowed_extensions
            and self.max_length == other.max_length
        )


@deconstructible
class DocumentFileNameValidator(RegexValidator):
    """
    Validate a document file name against an explicit allowlist of extensions.

    Pass only the extensions you accept for the endpoint, typically two or three
    (for example ``DocumentFileNameValidator(['pdf', 'docx'])``).
    """

    message = _('This document file is not supported. Please upload another document.')
    regex = r'^[^/\\?%*:|"<>\x00]+$'

    def __init__(self, allowed_extensions, *, max_length: int = 255):
        super().__init__()
        if not allowed_extensions:
            raise ValueError('allowed_extensions must not be empty')

        normalized = {
            extension.lower().removeprefix('.')
            for extension in allowed_extensions
        }
        if not normalized:
            raise ValueError('allowed_extensions must not be empty')

        self.max_length = max_length
        self.allowed_extensions = frozenset(normalized)

    def __call__(self, value: str):
        if not isinstance(value, str) or len(value) > self.max_length:
            raise ValidationError(self.message, code=self.code, params={"value": value})

        super().__call__(value)

        if '.' not in value:
            raise ValidationError(self.message, code=self.code, params={"value": value})

        name, extension = value.rsplit('.', 1)
        if not name or extension.lower() not in self.allowed_extensions:
            raise ValidationError(self.message, code=self.code, params={"value": value})

    def __eq__(self, other):
        return (
            isinstance(other, DocumentFileNameValidator)
            and super().__eq__(other)
            and self.allowed_extensions == other.allowed_extensions
            and self.max_length == other.max_length
        )
