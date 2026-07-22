from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


def send_templated_email(
    *,
    subject: str,
    html_template: str,
    to: list[str],
    context: dict,
    from_email: str | None = None,
) -> int:
    """
    Render an HTML body template and send via Django's email backend.

    Returns the number of successfully delivered messages (0 or 1 for a single send).
    """
    html_body = render_to_string(html_template, context)
    message = EmailMultiAlternatives(
        subject=subject,
        body=html_body,
        from_email=from_email or settings.DEFAULT_FROM_EMAIL,
        to=to,
    )
    message.content_subtype = "html"
    return message.send(fail_silently=False)
