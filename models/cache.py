from collections import UserDict
from dataclasses import dataclass
from hashlib import sha256
from itertools import chain
from typing import Dict, List, Any, Callable, Union, Iterable, Optional, Type

from django.core.cache import caches, BaseCache, InvalidCacheBackendError

from wagtail.models import Page


__all__ = ['CacheMeta', 'UnknownCachePrefixException', 'CachePrefixDict', 'AbstractCacheAware',
           'AbstractCacheAwarePage', 'CacheProvider', ]


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


class CacheProvider:

    CACHE_ACTION_NONE: int = 0
    CACHE_ACTION_CLEAR: int = 1
    CACHE_EXTRA_DELIMITER: str = ';'
    CACHE_EXTRA_SALT: str = 'extra'

    CACHE_POLICIES: Dict[str, int] = {
        'save': CACHE_ACTION_CLEAR,
        'delete': CACHE_ACTION_CLEAR,
    }

    def __init__(self, cache_prefixes: CachePrefixDict):
        self._cache_prefixes: CachePrefixDict = cache_prefixes

    @staticmethod
    def _get_instance(alias: Union[str, Iterable[str]]) -> BaseCache:
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

    def clear(self, vary_on: Optional[Iterable[Any]] = None) -> None:
        aliases_keys: Dict[str, List[str]] = dict()

        for prefix, meta in self._cache_prefixes.items():
            aliases: Iterable[str] = [meta.alias, ] if type(meta.alias) == str else meta.alias
            a: str
            extra_key: str = self.get_extra_key(prefix, vary_on)
            extra_keys: list[str]
            extra_keys_str: str
            keys: list[str] = [self.get_key(prefix, vary_on)]

            for a in aliases:
                if a in aliases_keys:
                    aliases_keys[a].extend(keys)
                else:
                    aliases_keys[a] = keys

                aliases_keys[a].append(extra_key)

                try:
                    extra_keys_str = caches[a].get(extra_key)
                except InvalidCacheBackendError:
                    extra_keys = []
                else:
                    extra_keys = extra_keys_str.split(self.CACHE_EXTRA_DELIMITER) if extra_keys_str else []

                aliases_keys[a].extend(extra_keys)

        for alias, keys in aliases_keys.items():
            try:
                caches[alias].delete_many(keys)
            except InvalidCacheBackendError:
                pass

    def get_data(self, prefix: str, vary_on: Optional[Iterable[Any]] = None,
                 extra: Optional[Iterable[Any]] = None) -> Any:
        return self._get_instance(self.get_meta(prefix).alias).get(
            self.get_key(prefix, vary_on, extra)
        )

    @classmethod
    def get_extra_key(cls, prefix: str, vary_on: Optional[Iterable[Any]] = None) -> str:
        return cls.get_hash(chain([prefix, cls.CACHE_EXTRA_SALT], vary_on if vary_on is not None else []))

    @staticmethod
    def get_hash(items: Iterable[Any]) -> str:
        hasher = sha256()
        is_empty: bool = True

        for i in items:
            hasher.update(str(i).encode())
            is_empty = False

        return '' if is_empty else hasher.hexdigest()

    @classmethod
    def get_key(cls, prefix: str, vary_on: Optional[Iterable[Any]] = None,
                extra: Optional[Iterable[Any]] = None) -> str:
        return cls.get_hash(chain([prefix], vary_on if vary_on is not None else [], extra if extra is not None else []))

    def get_meta(self, prefix: str) -> CacheMeta:
        try:
            return self._cache_prefixes[prefix]
        except KeyError as e:
            raise UnknownCachePrefixException from e

    def get_or_set_data(self, prefix: str, data_callable: Callable, vary_on: Optional[Iterable[Any]] = None,
                        extra: Optional[Iterable[Any]] = None) -> Any:
        data: Any = self.get_data(prefix, vary_on, extra)

        if data is None:
            data = data_callable()
            self.set_data(prefix, data, vary_on, extra)

        return data

    def set_data(self, prefix: str, data: Any, vary_on: Optional[Iterable[Any]] = None,
                 extra: Optional[Iterable[Any]] = None) -> None:
        meta: CacheMeta = self.get_meta(prefix)
        cache_instance: BaseCache = self._get_instance(meta.alias)
        cache_key: str = self.get_key(prefix, vary_on, extra)
        cache_instance.set(cache_key, data, meta.lifetime)

        if extra:
            extra_key: str = self.get_extra_key(prefix, vary_on)
            extra_data: str = cache_instance.get(extra_key)

            if extra_data:
                extra_list: list[str] = extra_data.split(self.CACHE_EXTRA_DELIMITER)
                if cache_key not in extra_list:
                    extra_list.append(cache_key)
                    extra_data = self.CACHE_EXTRA_DELIMITER.join(extra_list)
            else:
                extra_data = cache_key

            cache_instance.set(extra_key, extra_data, meta.lifetime)


class AbstractCacheAware:

    _cache_provider: Optional[CacheProvider] = None
    cache_prefixes: CachePrefixDict = CachePrefixDict()
    cache_provider_class: Type[CacheProvider] = CacheProvider
    cache_template_prefix: Optional[str] = None

    @classmethod
    def get_cache_provider(cls) -> CacheProvider:
        if cls._cache_provider is None:
            cls._cache_provider = cls.cache_provider_class(cls.cache_prefixes)

        return cls._cache_provider

    @classmethod
    def get_cache_template_prefix(cls) -> Optional[str]:
        return cls.cache_template_prefix

    def get_cache_vary_on(self) -> Iterable[Any]:
        raise NotImplementedError

    def get_cache_dependents(self) -> Optional[Iterable['AbstractCacheAware']]:
        return


class AbstractCacheAwarePage(AbstractCacheAware, Page):

    class Meta:
        abstract = True

    def get_cache_vary_on(self) -> Iterable[Any]:
        return self.pk,
