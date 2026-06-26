from django.db import models
from django.utils.translation import gettext_lazy as _


class NovelStatus(models.TextChoices):
    DRAFT = "draft", _("Draft")
    INCOMPLETE = "incomplete", _("Incomplete")
    COMPLETED = "completed", _("Completed")

class ChapterStatus(models.TextChoices):
    DRAFT = "draft", _("Draft")
    PUBLISHED = "published", _("Published")
