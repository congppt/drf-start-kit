from django.core.validators import validate_slug, validate_unicode_slug

class SlugValidator:
    def __call__(self, value):
        validate_slug(value)

class UnicodeSlugValidator:
    def __call__(self, value):
        validate_unicode_slug(value)