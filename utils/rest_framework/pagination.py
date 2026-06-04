from rest_framework.pagination import LimitOffsetPagination

class SafeLimitOffsetPagination(LimitOffsetPagination):
    max_limit = 100