import django_filters
from django.db.models import Value
from django.db.models.functions import Concat
from rest_framework import viewsets

from .. import models, permissions, serializers


class NovelFilter(django_filters.FilterSet):
    genres = django_filters.ModelMultipleChoiceFilter(queryset=models.Genre.objects.all(), conjoined=True)

    class Meta:
        model = models.Novel
        fields = ["status"]
        

class NovelViewSet(viewsets.ModelViewSet):
    queryset = (
        models.Novel.objects
        .select_related("author")
        .prefetch_related("genres", "attachments__file")
        .annotate(author_name=Concat('author__first_name', Value(' '), 'author__last_name'))
        .all()
    )
    permission_classes = [permissions.DjangoModelPermissions]
    serializer_class = serializers.NovelSerializer
    filterset_class = NovelFilter
    search_fields = ["title", "blurb", "author_name"]