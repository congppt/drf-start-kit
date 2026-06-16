from rest_framework.pagination import LimitOffsetPagination


class Max100LimitOffsetPagination(LimitOffsetPagination):
    max_limit = 100
