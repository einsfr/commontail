from django.test import TestCase

from commontail.models.cache import AbstractCacheAware, CacheSuffixDict


class TestCacheAware(AbstractCacheAware):

    def get_cache_prefix(self) -> str:
        return 'test'


class TestCache(TestCase):

    def test_cache_suffix_dict(self):
        d1 = CacheSuffixDict({1: 'a', 2: 'b'})
        d2 = {1: 'c', 3: 'd'}
        d3 = CacheSuffixDict(d2)

        self.assertEqual({1: 'c', 2: 'b', 3: 'd'}, d1 + d2)
        self.assertEqual({1: 'c', 2: 'b', 3: 'd'}, d1 + d3)

