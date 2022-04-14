from typing import Sequence


__all__ = ['ru_plural', ]


def ru_plural(int_value: int, variants: Sequence[str]) -> str:
    if len(variants) < 3:
        variants = list(variants) + ['' for _ in range(0, 3 - len(variants))]
    if int_value in range(11, 15):
        return variants[2]
    else:
        mod_value = int_value % 10
        if mod_value == 1:
            return variants[0]
        elif mod_value in range(2, 5):
            return variants[1]
        else:
            return variants[2]
