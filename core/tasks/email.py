from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import gettext as _
from huey.contrib import djhuey

from integrations.email import send_templated_email
from utils.log import logger

from .. import models


@djhuey.db_task()
def send_password_reset_email(user_id: int) -> None:
    user = models.User.objects.filter(pk=user_id, is_active=True).first()
    if not user or not user.email or not user.has_usable_password():
        return

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    reset_url = f"{settings.FRONTEND_URL}/reset-password?uid={uid}&token={token}"

    send_templated_email(
        subject=_("Password reset"),
        html_template="email/password_reset_body.html",
        to=[user.email],
        context={
            "user": user,
            "reset_url": reset_url,
            "uid": uid,
            "token": token,
        },
    )
    logger.info("Password reset email sent", extra={"user_id": user.pk})
