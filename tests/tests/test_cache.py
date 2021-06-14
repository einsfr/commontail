from django.test import TestCase
from django.core.cache import InvalidCacheBackendError, cache

from commontail.models.cache import AbstractCacheAware, CacheSuffixDict, CacheSuffixMeta, UnknownCacheSuffixException

from ..models import CacheAwareModel


class TestCacheAware(AbstractCacheAware):

    cache_suffixes = AbstractCacheAware.cache_suffixes + {
        'test1': CacheSuffixMeta('default', 300),
        'test2': CacheSuffixMeta('nonexistent', 300),
    }

    def get_cache_prefix(self) -> str:
        return 'test'


class TestCache(TestCase):

    def test_cache_suffix_dict(self):
        d1 = CacheSuffixDict({1: 'a', 2: 'b'})
        d2 = {1: 'c', 3: 'd'}
        d3 = CacheSuffixDict(d2)

        self.assertEqual({1: 'c', 2: 'b', 3: 'd'}, d1 + d2)
        self.assertEqual({1: 'c', 2: 'b', 3: 'd'}, d1 + d3)

    def test_cache_aware(self):
        cache_aware = TestCacheAware()

        for f in [
            lambda: cache_aware.clear_cache(),
            lambda: cache_aware.delete_cache_suffix('test2'),
            lambda: cache_aware.get_cache_data('test2'),
            lambda: cache_aware.get_or_set_cache_data('test2', lambda: True),
            lambda: cache_aware.set_cache_data('test2', lambda: True),
        ]:
            with self.assertRaises(InvalidCacheBackendError):
                f()

        TestCacheAware.cache_suffixes.pop('test2')

        cache_aware.set_cache_data('test1', True)
        self.assertTrue(cache.get('test__test1'))
        self.assertTrue(cache_aware.get_cache_data('test1'))
        cache_aware.delete_cache_suffix('test1')
        self.assertIsNone(cache_aware.get_cache_data('test1'))
        self.assertTrue(cache_aware.get_or_set_cache_data('test1', lambda: True))
        self.assertTrue(cache.get('test__test1'))

        with self.assertRaises(UnknownCacheSuffixException):
            cache_aware.get_cache_meta('nonexistent')

    def test_cache_signals(self):
        cache_aware_instance = CacheAwareModel.objects.create()
        cache_aware_instance.set_cache_data('test', cache_aware_instance.pk)
        self.assertEqual(cache.get(f'testmodel{cache_aware_instance.pk}__test'), cache_aware_instance.pk)
        cache_aware_instance.save()
        self.assertIsNone(cache.get(f'testmodel{cache_aware_instance.pk}__test'))
        cache_aware_instance.set_cache_data('test', cache_aware_instance.pk)
        cache_aware_instance = CacheAwareModel.objects.all().first()
        self.assertEqual(cache_aware_instance.get_cache_data('test'), cache_aware_instance.pk)
