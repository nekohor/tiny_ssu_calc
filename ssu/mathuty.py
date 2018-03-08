# -*- coding: utf-8 -*-


def clamp(n, small, large):
    return max(small, min(n, large))


def clamp_old(aim_val, min_val, max_val):
    if aim_val <= min_val:
        return min_val
    elif aim_val >= max_val:
        return max_val
    else:
        return aim_val
