from dataclasses import dataclass

from django.utils import timezone

from ... import models, services


def admin_credit(
    *,
    recipient: models.User,
    sender: models.User,
    amount: int,
    note: str | None = None,
):
    timestamp = timezone.now().strftime("%y%m%d%H%M%S")
    idempotency_key = models.WalletLedgerEntryType.ADMIN_ADJUSTMENT.idempotency_key(
        timestamp=timestamp,
        sender_user_id=sender.pk,
        recipient_user_id=recipient.pk,
    )
    _, replayed = services.wallet.credit(
        recipient,
        amount,
        entry_type=models.WalletLedgerEntryType.ADMIN_ADJUSTMENT,
        idempotency_key=idempotency_key,
        note=note,
    )
    return not replayed
