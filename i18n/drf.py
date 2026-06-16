from django.utils.translation import gettext_lazy as _

DRF_MESSAGE_OVERRIDES = (
    _("Authentication credentials were not provided."),
    _("Incorrect authentication credentials."),
    _("You do not have permission to perform this action."),
    _("Not found."),
    _('Method "{method}" not allowed.'),
    _("Could not satisfy the request Accept header."),
    _('Unsupported media type "{media_type}" in request.'),
    _("Request was throttled."),
)
