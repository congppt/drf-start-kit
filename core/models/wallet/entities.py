from django.db import models

from ..user import User
from .enums import WalletLedgerEntryType


class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="wallet")
    balance = models.PositiveBigIntegerField(default=0)


class WalletLedgerEntry(models.Model):
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="ledger_entries")
    amount = models.IntegerField()
    balance_after = models.PositiveBigIntegerField()
    type = models.CharField(max_length=20, choices=WalletLedgerEntryType.choices, db_index=True)
    idempotency_key = models.CharField(max_length=128, unique=True)
    note = models.TextField(null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)