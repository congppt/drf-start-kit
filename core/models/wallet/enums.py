from django.db import models


class WalletLedgerEntryType(models.TextChoices):
    REWARD = "reward"
    CHAPTER_PURCHASE = "chapter_purchase"
    ADMIN_ADJUSTMENT = "admin_adjustment"
    TOP_UP = "top_up"

    @property
    def idempotency_key_format(self) -> str | None:
        return {
            WalletLedgerEntryType.CHAPTER_PURCHASE: "{ledger_type}:{user_id}:{chapter_id}",
        }.get(self)

    def idempotency_key(self, **kwargs) -> str:
        fmt = self.idempotency_key_format
        if fmt is None:
            raise TypeError(f"{self!r} does not define a server-side idempotency key.")
        return fmt.format(ledger_type=self.value, **kwargs)
