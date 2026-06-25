from rest_framework.pagination import LimitOffsetPagination

__CACHE = {}


def limit_offset_class(maximum_limit: int | None = 100):
    """
    Create a custom limit offset pagination class with a maximum limit.
    Arguments:
        maximum_limit: The maximum limit for the pagination.
        If None, there is no maximum limit.`
    Returns:
        A custom limit offset pagination class.
    """
    class_name = f"Max{maximum_limit}LimitOffsetPagination"
    if class_name in __CACHE:
        return __CACHE[class_name]

    class CustomLimitOffsetPagination(LimitOffsetPagination):
        max_limit = maximum_limit

    CustomLimitOffsetPagination.__name__ = class_name
    CustomLimitOffsetPagination.__qualname__ = class_name
    __CACHE[class_name] = CustomLimitOffsetPagination
    return CustomLimitOffsetPagination
