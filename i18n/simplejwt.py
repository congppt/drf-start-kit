from django.utils.translation import gettext_lazy as _


SIMPLEJWT_MESSAGE_OVERRIDES = (
    _('Authorization header must contain two space-delimited values'),
    _('Given token not valid for any token type'),
    _('Token contained no recognizable user identification'),
    _('User not found'),
    _('User is inactive'),
    _("The user's password has been changed."),
    _('Token is invalid'),
    _('Token is expired'),
    _('Token is invalid or expired'),
    _('No active account found with the given credentials'),
    _('No active account found for the given token.'),
    _('Token is blacklisted'),
    _('Cannot create token with no type or lifetime'),
    _('Token has no id'),
    _('Token has no type'),
    _('Token has wrong type'),
    _("Token has no '{}' claim"),
    _("Token '{}' claim has expired"),
)
