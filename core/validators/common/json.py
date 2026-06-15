from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _


@deconstructible
class JSONSchemaValidator:
    """
    Validate a dict against a schema mapping keys to types and/or validators.

    By default only keys present in the input are checked and extra keys are
    allowed. Set ``strict=True`` to reject keys that are not declared in the
    schema.
    """

    message = _('Invalid value for key "%(key)s".')
    type_message = _('Expected %(expected)s, got %(actual)s.')
    extra_keys_message = _('Unexpected keys: %(keys)s.')

    def __init__(self, schema: dict, *, strict: bool = False):
        self.schema = schema
        self.strict = strict

    def __call__(self, value: dict):
        if not isinstance(value, dict):
            raise ValidationError(
                _('Expected a JSON object.'),
                code='invalid',
                params={'value': value},
            )

        if self.strict:
            extra_keys = sorted(set(value) - set(self.schema))
            if extra_keys:
                raise ValidationError(
                    self.extra_keys_message,
                    code='extra_keys',
                    params={'keys': ', '.join(extra_keys)},
                )

        errors = []
        for key, constraint in self.schema.items():
            if key not in value:
                continue
            try:
                self._validate_item(value[key], constraint)
            except ValidationError as exc:
                if hasattr(exc, 'error_list'):
                    for error in exc.error_list:
                        errors.append(ValidationError(
                            error.message,
                            code=error.code,
                            params={**(error.params or {}), 'key': key},
                        ))
                else:
                    errors.append(ValidationError(
                        self.message,
                        code=exc.code or 'invalid',
                        params={'key': key, 'value': value[key]},
                    ))

        if errors:
            raise ValidationError(errors)

    def _validate_item(self, item, constraint):
        if isinstance(constraint, type):
            if constraint is bool and not isinstance(item, bool):
                raise ValidationError(
                    self.type_message,
                    code='invalid',
                    params={'expected': 'bool', 'actual': type(item).__name__},
                )
            if constraint is not bool and not isinstance(item, constraint):
                raise ValidationError(
                    self.type_message,
                    code='invalid',
                    params={'expected': constraint.__name__, 'actual': type(item).__name__},
                )
            return

        if isinstance(constraint, JSONSchemaValidator):
            constraint(item)
            return

        if callable(constraint):
            constraint(item)
            return

        raise TypeError(
            f'JSONSchemaValidator schema values must be types, validators, or '
            f'JSONSchemaValidator instances, not {type(constraint).__name__}.'
        )

    def __eq__(self, other):
        return (
            isinstance(other, JSONSchemaValidator)
            and self.schema == other.schema
            and self.strict == other.strict
        )
