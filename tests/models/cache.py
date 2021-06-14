from django.db import models

from commontail.models import AbstractCacheAware, CacheSuffixMeta


__all__ = ['CacheAwareModel', ]


class CacheAwareModel(AbstractCacheAware, models.Model):

    cache_suffixes = AbstractCacheAware.cache_suffixes + {
        'test': CacheSuffixMeta('default', 300),
    }

    def get_cache_prefix(self) -> str:
        return f'testmodel{self.pk}'
