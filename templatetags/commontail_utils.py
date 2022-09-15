from typing import Collection, Iterable, Union, List

from django import template


register = template.Library()


@register.filter
def evenlysplit(value: Union[Collection, Iterable], count: int) -> List[list]:
    value_length: int
    try:
        value_length = len(value)
    except TypeError:
        value = list(value)
        value_length = len(value)

    min_chunk_size: int = int(value_length / count)
    maximized_chunks_count: int = value_length - min_chunk_size * count
    chunks: List[list] = []
    current_chunk: list = []

    for item in value:
        if len(current_chunk) < min_chunk_size:
            current_chunk.append(item)
        else:
            if len(chunks) < maximized_chunks_count:
                current_chunk.append(item)
                chunks.append(current_chunk)
                current_chunk = []
            else:
                chunks.append(current_chunk)
                current_chunk = [item]

    chunks.append(current_chunk)

    return chunks
