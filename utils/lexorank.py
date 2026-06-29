__ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyz"  # 36 characters
__LEXORANK_BASE = len(__ALPHABET)
__RANK_LENGTH = 8

# Khoảng cách nhảy bậc mặc định (Step) khi dùng hàm gen_next hoặc gen_prev
__DEFAULT_STEP_BASE10 = __LEXORANK_BASE**4  # Bằng 1.679.616 trong hệ thập phân


def __to_base10(pos: str) -> int:
    val = 0
    for char in pos:
        val = val * __LEXORANK_BASE + __ALPHABET.index(char)
    return val


def __to_lexorank_base(num: int, min_length: int) -> str:
    if num <= 0:
        return "0".zfill(min_length)
    res = []
    while num > 0:
        res.append(__ALPHABET[num % __LEXORANK_BASE])
        num //= __LEXORANK_BASE
    return "".join(reversed(res)).zfill(min_length)


def __parse(rank: str):
    bucket, pos = rank.split("|")
    return int(bucket), pos


def __format(bucket: int, pos: str) -> str:
    return f"{bucket}|{pos}"


def __gen_next_pos(pos: str) -> str:
    val = __to_base10(pos)
    max_val = __to_base10("z" * len(pos))

    if val + __DEFAULT_STEP_BASE10 >= max_val:
        return pos + __ALPHABET[__LEXORANK_BASE // 2]
    return __to_lexorank_base(val + __DEFAULT_STEP_BASE10, len(pos))


def __gen_prev_pos(pos: str) -> str:
    val = __to_base10(pos)
    if val - __DEFAULT_STEP_BASE10 <= 0:
        return "0" + pos
    return __to_lexorank_base(val - __DEFAULT_STEP_BASE10, len(pos))


def get_rank(prev_rank: str | None, next_rank: str | None) -> str:
    if not prev_rank and not next_rank:
        initial_midpoint = (__LEXORANK_BASE**__RANK_LENGTH) // 2
        return __format(0, __to_lexorank_base(initial_midpoint, __RANK_LENGTH))

    if not prev_rank and next_rank:
        bucket, pos = __parse(next_rank)
        return __format(bucket, __gen_prev_pos(pos))

    if prev_rank and not next_rank:
        bucket, pos = __parse(prev_rank)
        return __format(bucket, __gen_next_pos(pos))

    prev_bucket, prev_pos = __parse(prev_rank)
    next_bucket, next_pos = __parse(next_rank)

    if prev_bucket != next_bucket:
        raise ValueError("Cannot use this function for 2 different buckets!")

    # Pad the positions to the same length
    max_len = max(len(prev_pos), len(next_pos))
    prev_pos = prev_pos.ljust(max_len, "0")
    next_pos = next_pos.ljust(max_len, "0")

    prev_value = __to_base10(prev_pos)
    next_value = __to_base10(next_pos)

    # If the difference between the values is 1, we need to increment the positions length by 1 to get a valid integer mid value
    if next_value - prev_value <= 1:
        prev_pos += "0"
        next_pos += "0"
        max_len += 1
        prev_value = __to_base10(prev_pos)
        next_value = __to_base10(next_pos)

    mid_value = (prev_value + next_value) // 2
    mid_pos = __to_lexorank_base(mid_value, max_len)
    return __format(prev_bucket, mid_pos)
