from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.utils.translation import gettext_lazy as _

from .. import common
from ..user import User
from ..wallet import WalletLedgerEntry
from .enums import NovelStatus


class Genre(models.Model):
    label = models.CharField(unique=True, max_length=30)
    color = models.CharField(max_length=7)

    def __str__(self):
        return self.label


class Novel(common.AuditableModel):
    title = models.CharField(max_length=80)
    slug = models.SlugField(unique=True, max_length=100)
    blurb = models.TextField()
    genres = models.ManyToManyField(Genre, related_name="novels")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="novels")
    status = models.CharField(choices=NovelStatus.choices, default=NovelStatus.DRAFT, db_index=True)
    last_publication_at = models.DateTimeField(null=True, db_index=True)
    attachments = GenericRelation(common.FileAttachment)
    default_chapter_price = models.PositiveIntegerField(default=0)

    COVER_FIELD_NAME = "cover"

    def __str__(self):
        return self.title


class Chapter(common.AuditableModel):
    novel = models.ForeignKey(Novel, on_delete=models.CASCADE, related_name="chapters")
    lexorank = models.CharField(max_length=20, db_index=True)
    title = models.CharField(max_length=80)
    content = models.TextField()
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True)
    price = models.PositiveIntegerField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=["novel", "lexorank"], name="uq_novel_lexorank")]

    def __str__(self):
        return self.title


class ChapterPurchase(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chapter_purchases")
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name="purchases")
    ledger = models.OneToOneField(WalletLedgerEntry, on_delete=models.CASCADE, related_name="chapter_purchase")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "chapter"], name="uq_chapterpurchase_user_chapter")]


class ReadingProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reading_progresses")
    novel = models.ForeignKey(Novel, on_delete=models.CASCADE, related_name="reading_progresses")
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name="reading_progresses")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "novel"], name="uq_readingprogress_user_novel")]


class NovelReadEvent(models.Model):
    novel = models.ForeignKey(Novel, on_delete=models.CASCADE, related_name="read_events")
    viewer_id = models.CharField(max_length=64, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["novel", "viewer_id"], name="uq_novel_viewer")]

    CREATE_RESTRICTED_SECONDS = 60 * 60 * 24  # 24 hours


class Bookmark(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bookmarks")
    novel = models.ForeignKey(Novel, on_delete=models.CASCADE, related_name="bookmarks")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "novel"], name="uq_bookmark_user_novel")]
