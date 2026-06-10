from rest_framework.pagination import LimitOffsetPagination

def limit_offset_class_factory(maximum_limit: int | None = 100):
    """
    Create a custom limit offset pagination class with a maximum limit.
    Arguments:
        maximum_limit: The maximum limit for the pagination.
        If None, there is no maximum limit.`
    Returns:
        A custom limit offset pagination class.
    """
    class CustomLimitOffsetPagination(LimitOffsetPagination):
        max_limit = maximum_limit
    return CustomLimitOffsetPagination

class SafeLimitOffsetPagination(LimitOffsetPagination):
    max_limit = 100