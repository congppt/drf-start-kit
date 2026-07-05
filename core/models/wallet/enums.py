from django.db import models


class WalletLedgerEntryType(models.TextChoices):
    REWARD = "reward"
    CHAPTER_PURCHASE = "chapter_purchase"
    ADMIN_ADJUSTMENT = "admin_adjustment"
    TOP_UP = "top_up"
