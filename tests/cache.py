from typing import Iterable, Any

from django.test import SimpleTestCase

from ..models.cache import AbstractCacheAware, CacheMeta, UnknownCachePrefixException


__all__ = ['CacheTestCase', ]


TEST_PREFIX = 'test_prefix'


class CacheAwareModel(AbstractCacheAware):

    def __init__(self, vary: int):
        self.vary: int = vary

    cache_prefixes = AbstractCacheAware.cache_prefixes + {
        TEST_PREFIX: CacheMeta('default', 60),
    }

    def get_cache_vary_on(self) -> Iterable[Any]:
        return self.vary,


class CacheTestCase(SimpleTestCase):

    EXTRA1 = ['abc', 123]
    EXTRA1_HASH = '54aff04272ca5ee598edc979279638d9571180bd'

    EXTRA2 = [32546]
    EXTRA2_HASH = 'bb47cc1606caa655e8f9b8263a38ca4222e64220'

    VARY_ON1 = ['abc']
    VARY_ON1_HASH = '7fe0b7d5db5df8356de40b0fc54884846a66d386'

    VARY_ON2 = ['def', 456]

    TEST_INT = 16845
    TEST_STR = 'some test data'

    def test_get_cache_hash(self):
        self.assertEqual('', CacheAwareModel.get_cache_provider().get_hash([]))
        self.assertEqual('', CacheAwareModel.get_cache_provider().get_hash((i for i in [])))
        self.assertEqual(self.VARY_ON1_HASH, CacheAwareModel.get_cache_provider().get_hash(self.VARY_ON1))
        self.assertEqual(self.EXTRA1_HASH, CacheAwareModel.get_cache_provider().get_hash(self.EXTRA1))

    def test_get_key(self):
        self.assertEqual(
            (TEST_PREFIX, '', ''),
            CacheAwareModel.get_cache_provider().get_key_parts(TEST_PREFIX)
        )
        self.assertEqual(
            (TEST_PREFIX, self.VARY_ON1_HASH, ''),
            CacheAwareModel.get_cache_provider().get_key_parts(TEST_PREFIX, vary_on=self.VARY_ON1)
        )
        self.assertEqual(
            (TEST_PREFIX, '', self.EXTRA1_HASH),
            CacheAwareModel.get_cache_provider().get_key_parts(TEST_PREFIX, extra=self.EXTRA1)
        )
        self.assertEqual(
            (TEST_PREFIX, self.VARY_ON1_HASH, self.EXTRA1_HASH),
            CacheAwareModel.get_cache_provider().get_key_parts(TEST_PREFIX, self.VARY_ON1, self.EXTRA1)
        )

        self.assertEqual(
            f'{TEST_PREFIX}__',
            CacheAwareModel.get_cache_provider().get_key(TEST_PREFIX)
        )
        self.assertEqual(
            f'{TEST_PREFIX}_{self.VARY_ON1_HASH}_',
            CacheAwareModel.get_cache_provider().get_key(TEST_PREFIX, vary_on=self.VARY_ON1)
        )
        self.assertEqual(
            f'{TEST_PREFIX}__{self.EXTRA1_HASH}',
            CacheAwareModel.get_cache_provider().get_key(TEST_PREFIX, extra=self.EXTRA1)
        )
        self.assertEqual(
            f'{TEST_PREFIX}_{self.VARY_ON1_HASH}_{self.EXTRA1_HASH}',
            CacheAwareModel.get_cache_provider().get_key(TEST_PREFIX, vary_on=self.VARY_ON1, extra=self.EXTRA1)
        )

    def test_get_extra_key(self):
        self.assertEqual(
            f'{TEST_PREFIX}_{self.VARY_ON1_HASH}_extra',
            CacheAwareModel.get_cache_provider().get_extra_key(TEST_PREFIX, vary_on=self.VARY_ON1)
        )

    def test_get_instance(self):
        self.assertTrue(CacheAwareModel.get_cache_provider()._get_instance('default'))
        self.assertTrue(CacheAwareModel.get_cache_provider()._get_instance(('non-existent', 'default')))

    def test_cache_operations(self):
        self.assertRaises(
            UnknownCachePrefixException,
            lambda: CacheAwareModel.get_cache_provider().get_data('unknown_prefix')
        )

        self.assertIsNone(CacheAwareModel.get_cache_provider().get_data(TEST_PREFIX))
        CacheAwareModel.get_cache_provider().set_data(TEST_PREFIX, self.TEST_STR)
        self.assertEqual(
            self.TEST_STR,
            CacheAwareModel.get_cache_provider().get_data(TEST_PREFIX)
        )
        CacheAwareModel.get_cache_provider().clear()
        self.assertIsNone(CacheAwareModel.get_cache_provider().get_data(TEST_PREFIX))

        self.assertIsNone(CacheAwareModel.get_cache_provider().get_data(TEST_PREFIX, vary_on=self.VARY_ON1))
        CacheAwareModel.get_cache_provider().set_data(TEST_PREFIX, self.TEST_STR, vary_on=self.VARY_ON1)
        CacheAwareModel.get_cache_provider().set_data(TEST_PREFIX, self.TEST_INT, vary_on=self.VARY_ON2)
        self.assertEqual(
            self.TEST_STR,
            CacheAwareModel.get_cache_provider().get_data(TEST_PREFIX, vary_on=self.VARY_ON1)
        )
        self.assertEqual(
            self.TEST_INT,
            CacheAwareModel.get_cache_provider().get_data(TEST_PREFIX, vary_on=self.VARY_ON2)
        )
        CacheAwareModel.get_cache_provider().clear(self.VARY_ON1)
        self.assertIsNone(CacheAwareModel.get_cache_provider().get_data(TEST_PREFIX, vary_on=self.VARY_ON1))
        self.assertEqual(
            self.TEST_INT,
            CacheAwareModel.get_cache_provider().get_data(TEST_PREFIX, vary_on=self.VARY_ON2)
        )
        CacheAwareModel.get_cache_provider().clear(self.VARY_ON2)
        self.assertIsNone(CacheAwareModel.get_cache_provider().get_data(TEST_PREFIX, vary_on=self.VARY_ON2))

        self.assertIsNone(CacheAwareModel.get_cache_provider().get_data(
            TEST_PREFIX, vary_on=self.VARY_ON1, extra=self.EXTRA1))
        CacheAwareModel.get_cache_provider().set_data(
            TEST_PREFIX, self.TEST_STR, vary_on=self.VARY_ON1, extra=self.EXTRA1)
        self.assertEqual(
            self.TEST_STR,
            CacheAwareModel.get_cache_provider().get_data(TEST_PREFIX, vary_on=self.VARY_ON1,
                                                          extra=self.EXTRA1)
        )
        self.assertEqual(
            f'{TEST_PREFIX}_{self.VARY_ON1_HASH}_{self.EXTRA1_HASH}',
            CacheAwareModel.get_cache_provider()._get_instance('default').get(
                f'{TEST_PREFIX}_{self.VARY_ON1_HASH}_extra'
            )
        )
        CacheAwareModel.get_cache_provider().set_data(
            TEST_PREFIX, self.TEST_INT, vary_on=self.VARY_ON1, extra=self.EXTRA2)
        self.assertEqual(
            self.TEST_STR,
            CacheAwareModel.get_cache_provider().get_data(TEST_PREFIX, vary_on=self.VARY_ON1,
                                                          extra=self.EXTRA1)
        )
        self.assertEqual(
            self.TEST_INT,
            CacheAwareModel.get_cache_provider().get_data(TEST_PREFIX, vary_on=self.VARY_ON1,
                                                          extra=self.EXTRA2)
        )
        self.assertEqual(
            f'{TEST_PREFIX}_{self.VARY_ON1_HASH}_{self.EXTRA1_HASH};'
            f'{TEST_PREFIX}_{self.VARY_ON1_HASH}_{self.EXTRA2_HASH}',
            CacheAwareModel.get_cache_provider()._get_instance('default').get(
                f'{TEST_PREFIX}_{self.VARY_ON1_HASH}_extra'
            )
        )
        CacheAwareModel.get_cache_provider().clear(self.VARY_ON1)
        self.assertIsNone(CacheAwareModel.get_cache_provider().get_data(
            TEST_PREFIX, vary_on=self.VARY_ON1, extra=self.EXTRA1))
        self.assertIsNone(CacheAwareModel.get_cache_provider().get_data(
            TEST_PREFIX, vary_on=self.VARY_ON1, extra=self.EXTRA2))
        self.assertIsNone(CacheAwareModel.get_cache_provider()._get_instance('default').get(
            f'{TEST_PREFIX}_{self.VARY_ON1_HASH}_extra'
        ))
