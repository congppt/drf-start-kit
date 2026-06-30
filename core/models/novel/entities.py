from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.utils.translation import gettext_lazy as _

from ..common import AuditableModel, FileAttachment
from ..user import User
from .enums import NovelStatus


class Genre(models.Model):
    label = models.CharField(unique=True, max_length=30)
    color = models.CharField(max_length=7)

    def __str__(self):
        return self.label


class Novel(AuditableModel):
    title = models.CharField(max_length=80)
    slug = models.SlugField(unique=True, max_length=100)
    blurb = models.TextField()
    genres = models.ManyToManyField(Genre, related_name="novels")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="novels")
    status = models.CharField(choices=NovelStatus.choices, default=NovelStatus.DRAFT, db_index=True)
    attachments = GenericRelation(FileAttachment)

    COVER_FIELD_NAME = "cover"


class Chapter(AuditableModel):
    novel = models.ForeignKey(Novel, on_delete=models.CASCADE, related_name="chapters")
    lexorank = models.CharField(max_length=20, db_index=True)
    title = models.CharField(max_length=80)
    content = models.TextField()
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["novel", "lexorank"], name="uq_novel_lexorank")]

    def __str__(self):
        return self.title
