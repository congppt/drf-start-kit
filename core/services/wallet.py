from typing import Literal

from django.db import transaction
from django.db.models import F

from .. import models


class InsufficientBalanceError(Exception):
    pass


class WalletNotFoundError(Exception):
    pass


def _apply_balance_change(
    user: models.User,
    amount: int,
    *,
    direction: Literal[-1, 1],
    entry_type: models.WalletLedgerEntryType,
    idempotency_key: str,
    note: str | None,
) -> tuple[models.WalletLedgerEntry, bool]:
    existing = models.WalletLedgerEntry.objects.filter(idempotency_key=idempotency_key).first()
    if existing:
        return existing, True

    if amount <= 0:
        raise ValueError("Amount must be positive")

    with transaction.atomic():
        wallet = models.Wallet.objects.select_for_update().filter(user=user).first()
        if wallet is None:
            raise WalletNotFoundError

        if direction < 0:
            rows = models.Wallet.objects.filter(pk=wallet.pk, balance__gte=amount).update(
                balance=F("balance") - amount
            )
            if rows == 0:
                raise InsufficientBalanceError
        else:
            models.Wallet.objects.filter(pk=wallet.pk).update(balance=F("balance") + amount)

        wallet.refresh_from_db()
        replayed = False
        ledger, created = models.WalletLedgerEntry.objects.get_or_create(
            idempotency_key=idempotency_key,
            defaults={
                "wallet": wallet,
                "amount": direction * amount,
                "balance_after": wallet.balance,
                "type": entry_type,
                "note": note,
            },
        )
        if not created:
            transaction.set_rollback(True)
            replayed = True
    return ledger, replayed


def debit(
    user: models.User,
    amount: int,
    *,
    entry_type: models.WalletLedgerEntryType,
    idempotency_key: str,
    note: str | None = None,
) -> tuple[models.WalletLedgerEntry, bool]:
    """
    Debit wallet by amount. Returns (ledger_entry, replayed).
    replayed is True when idempotency_key already exists (no second debit).
    """
    return _apply_balance_change(
        user,
        amount,
        direction=-1,
        entry_type=entry_type,
        idempotency_key=idempotency_key,
        note=note,
    )


def credit(
    user: models.User,
    amount: int,
    *,
    entry_type: models.WalletLedgerEntryType,
    idempotency_key: str,
    note: str | None = None,
) -> tuple[models.WalletLedgerEntry, bool]:
    """
    Credit wallet by amount. Returns (ledger_entry, replayed).
    replayed is True when idempotency_key already exists (no second credit).
    """
    return _apply_balance_change(
        user,
        amount,
        direction=1,
        entry_type=entry_type,
        idempotency_key=idempotency_key,
        note=note,
    )
