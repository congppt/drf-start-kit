from dataclasses import dataclass

from django.db import transaction

from ... import models, services


@dataclass(frozen=True)
class PurchaseResult:
    purchase: models.ChapterPurchase
    created: bool


def purchase(*, user: models.User, chapter: models.Chapter) -> PurchaseResult:
    idempotency_key = models.WalletLedgerEntryType.CHAPTER_PURCHASE.idempotency_key(
        user_id=user.pk,
        chapter_id=chapter.pk,
    )

    with transaction.atomic():
        ledger, replayed = services.wallet.debit(
            user,
            chapter.price,
            entry_type=models.WalletLedgerEntryType.CHAPTER_PURCHASE,
            idempotency_key=idempotency_key,
            note=f"Chapter {chapter.pk}",
        )

        purchase, purchase_created = models.ChapterPurchase.objects.get_or_create(
            user=user,
            chapter=chapter,
            defaults={"ledger": ledger},
        )
        return PurchaseResult(purchase=purchase, created=purchase_created and not replayed)
