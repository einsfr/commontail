from collections import UserDict
from dataclasses import dataclass
from hashlib import sha1
from typing import Dict, List, Any, Callable, Union, Iterable, Optional

from django.core.cache import caches, BaseCache, InvalidCacheBackendError

from wagtail.core.models import Page


__all__ = ['CacheMeta', 'UnknownCachePrefixException', 'CachePrefixDict', 'AbstractCacheAware',
           'AbstractCacheAwarePage', ]


@dataclass
class CacheMeta:
    alias: Union[str, Iterable[str]]
    lifetime: int


class UnknownCachePrefixException(KeyError):
    pass


class CachePrefixDict(UserDict):

    def __add__(self, other):
        if not isinstance(other, (CachePrefixDict, dict)):
            raise TypeError(f"Unsupported operand type for +: CachePrefixDict and {type(other)}")
        result: CachePrefixDict = self.copy()
        result.update(other)

        return result


# TODO: Think about simple way to add cache dependency chains when one model change may invalidate many related caches
class AbstractCacheAware:

    CACHE_ACTION_NONE: int = 0
    CACHE_ACTION_CLEAR: int = 1

    CACHE_POLICIES: Dict[str, int] = {
        'save': CACHE_ACTION_CLEAR,
        'delete': CACHE_ACTION_CLEAR,
    }

    cache_prefixes: CachePrefixDict = CachePrefixDict()

    @staticmethod
    def _get_cache_instance(alias: Union[str, Iterable[str]]) -> BaseCache:
        if type(alias) == str:
            return caches[alias]
        else:
            a: str
            e: Optional[InvalidCacheBackendError] = None
            for a in alias:
                try:
                    return caches[a]
                except InvalidCacheBackendError as e:
                    pass

            if e is not None:
                raise e

    @classmethod
    def clear_cache(cls, vary_on: Optional[Iterable[Any]] = None) -> None:
        aliases_keys: Dict[str, List[str]] = dict()

        for prefix, meta in cls.cache_prefixes.items():
            alias: Iterable[str] = [meta.alias, ] if type(meta.alias) == str else meta.alias
            a: str
            for a in alias:
                if a in aliases_keys:
                    aliases_keys[a].append(cls.get_cache_key(prefix, vary_on))
                else:
                    aliases_keys[a] = [cls.get_cache_key(prefix, vary_on)]

        for alias, keys in aliases_keys.items():
            try:
                caches[alias].delete_many(keys)
            except InvalidCacheBackendError:
                pass

    @classmethod
    def get_cache_data(cls, prefix: str, vary_on: Optional[Iterable[Any]] = None) -> Any:
        return cls._get_cache_instance(cls.get_cache_meta(prefix).alias).get(cls.get_cache_key(prefix, vary_on))

    @classmethod
    def get_cache_key(cls, prefix: str, vary_on: Optional[Iterable[Any]] = None) -> str:
        key: str
        if vary_on is None:
            key = ''
        else:
            hasher = sha1()
            for v in vary_on:
                hasher.update(str(v).encode())
                hasher.update(b':')
            key = hasher.hexdigest()

        return f'{prefix}__{key}'

    @classmethod
    def get_cache_meta(cls, prefix: str) -> CacheMeta:
        try:
            return cls.cache_prefixes[prefix]
        except KeyError as e:
            raise UnknownCachePrefixException from e

    @classmethod
    def get_or_set_cache_data(cls, prefix: str, data_callable: Callable,
                              vary_on: Optional[Iterable[Any]] = None) -> Any:
        data: Any = cls.get_cache_data(prefix, vary_on)

        if data is None:
            data = data_callable()
            cls.set_cache_data(prefix, data, vary_on)

        return data

    @classmethod
    def set_cache_data(cls, prefix: str, data: Any, vary_on: Optional[Iterable[Any]] = None) -> None:
        meta: CacheMeta = cls.get_cache_meta(prefix)
        cls._get_cache_instance(meta.alias).set(cls.get_cache_key(prefix, vary_on), data, meta.lifetime)

    def get_cache_vary_on(self) -> Iterable[Any]:
        raise NotImplementedError


class AbstractCacheAwarePage(AbstractCacheAware, Page):

    class Meta:
        abstract = True

    def get_cache_vary_on(self) -> Iterable[Any]:
        return self.pk,
