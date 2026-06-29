from rest_framework import viewsets

from .. import models, permissions, serializers


class GenreViewSet(viewsets.ModelViewSet):
    queryset = models.Genre.objects.all()
    permission_classes = [permissions.DjangoModelPermissions]
    serializer_class = serializers.GenreSerializer
    search_fields = ["label"]