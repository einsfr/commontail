__all__ = ['get_cache_key', ]


def get_cache_key(prefix: str, *args) -> str:
    if not args:
        return prefix

    return f'{prefix}_{"_".join(map(str, args))}'
