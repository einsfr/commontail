import re

from typing import Union


__all__ = ['scale_resize_rule', ]


re_number_x_number: re.Pattern = re.compile(r'(\d+)x(\d+)')
re_number_eos: re.Pattern = re.compile(r'(\d+)$')


def scale_resize_rule(rule: str, ratio: Union[int, float]) -> str:
    match: re.Match = re_number_x_number.search(rule)

    if match:
        width: int = int(int(match.group(1)) * ratio)
        height: int = int(int(match.group(2)) * ratio)

        return f'{rule[:match.start(1)]}{width}x{height}{rule[match.end(2):]}'

    match: re.Match = re_number_eos.search(rule)

    if match:
        size: int = int(int(match.group(1)) * ratio)

        return f'{rule[:match.start(1)]}{size}'

    return ''
