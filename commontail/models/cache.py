from collections import namedtuple, UserDict
from typing import Dict, List, Any, Callable

from django.core.cache import caches, BaseCache

from wagtail.core.models import Page


__all__ = ['CacheSuffixMeta', 'UnknownCacheSuffixException', 'CacheSuffixDict', 'AbstractCacheAware',
           'AbstractCacheAwarePage', ]


CacheSuffixMeta = namedtuple('CacheSuffixMeta', ['alias', 'lifetime'])


class UnknownCacheSuffixException(KeyError):
    pass


class CacheSuffixDict(UserDict):

    def __add__(self, other):
        if not isinstance(other, (CacheSuffixDict, dict)):
            raise TypeError(f"Unsupported operand type for +: CacheSuffixDict and {type(other)}")
        result: CacheSuffixDict = self.copy()
        result.update(other)

        return result


class AbstractCacheAware:

    CACHE_ACTION_NONE: int = 0
    CACHE_ACTION_CLEAR: int = 1

    CACHE_POLICIES: Dict[str, int] = {
        'save': CACHE_ACTION_CLEAR,
        'delete': CACHE_ACTION_CLEAR,
    }

    cache_suffixes: CacheSuffixDict = CacheSuffixDict()

    def clear_cache(self) -> None:
        aliases_keys: Dict[str, List[str]] = dict()

        for suffix, meta in self.cache_suffixes.items():
            if meta.alias in aliases_keys:
                aliases_keys[meta.alias].append(self.get_cache_key(suffix))
            else:
                aliases_keys[meta.alias] = [self.get_cache_key(suffix)]

        for alias, keys in aliases_keys.items():
            caches[alias].delete_many(keys)

    def delete_cache_suffix(self, suffix: str) -> None:
        caches[self.get_cache_meta(suffix).alias].delete(self.get_cache_key(suffix))

    def get_cache_data(self, suffix: str) -> Any:
        return caches[self.get_cache_meta(suffix).alias].get(self.get_cache_key(suffix))

    def get_cache_key(self, suffix: str) -> str:
        return f'{self.get_cache_prefix()}__{suffix}'

    def get_cache_meta(self, suffix: str) -> CacheSuffixMeta:
        try:
            return self.cache_suffixes[suffix]
        except KeyError as e:
            raise UnknownCacheSuffixException from e

    def get_cache_prefix(self) -> str:
        raise NotImplementedError

    def get_or_set_cache_data(self, suffix: str, data_callable: Callable) -> Any:
        data: Any = self.get_cache_data(suffix)

        if data is None:
            data = data_callable()
            self.set_cache_data(suffix, data)

        return data

    def set_cache_data(self, suffix: str, data: Any) -> None:
        meta: CacheSuffixMeta = self.get_cache_meta(suffix)
        cache: BaseCache = caches[meta.alias]
        cache.set(self.get_cache_key(suffix), data, meta.lifetime)


class AbstractCacheAwarePage(AbstractCacheAware, Page):

    class Meta:
        abstract = True

    def get_cache_prefix(self) -> str:
        return f'page{self.pk}'
