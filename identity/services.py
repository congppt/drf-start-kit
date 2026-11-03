from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

from user.models import User


def blacklist_outstanding_refresh_tokens(user: User) -> None:
    BlacklistedToken.objects.bulk_create(
        [
            BlacklistedToken(token_id=token_id)
            for token_id in OutstandingToken.objects.filter(user=user).values_list("pk", flat=True)
        ],
        ignore_conflicts=True,
    )