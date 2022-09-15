from typing import Iterable, Any

from django.test import SimpleTestCase

from commontail.models.cache import AbstractCacheAware, CacheMeta, UnknownCachePrefixException


__all__ = ['CacheTestCase', ]


TEST_PREFIX = 'test_prefix'


class CacheAwareModel(AbstractCacheAware):

    def __init__(self, vary: int):
        self.vary: int = vary

    cache_prefixes = AbstractCacheAware.cache_prefixes + {
        TEST_PREFIX: CacheMeta(('template_fragments', 'default'), 60),
    }

    def get_cache_vary_on(self) -> Iterable[Any]:
        return self.vary,


class CacheTestCase(SimpleTestCase):

    EXTRA1 = ['abc', 123]
    EXTRA1_HASH = '6ca13d52ca70c883e0f0bb101e425a89e8624de51db2d2392593af6a84118090'

    EXTRA2 = [32546]
    EXTRA2_HASH = 'bb47cc1606caa655e8f9b8263a38ca4222e64220'

    VARY_ON1 = ['abc']
    VARY_ON1_HASH = 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'

    VARY_ON2 = ['def', 456]

    TEST_INT = 16845
    TEST_STR = 'some test data'

    TEST_PREFIX_HASH = 'f36e0369fdb6d2c6a5e6a4a0b741c3211285fca96856fa262f8395405e66e94f'
    TEST_PREFIX_VARY_ON1_HASH = 'fd02db8cbac5d36edc2d2fe3b77ea48be4996e469555f957627700d25b5478e2'
    TEST_PREFIX_VARY_ON1_EXTRA_HASH = '9a80b03fa55852f43d4f93a504c7dc23a455471bd293d1d54cbd270403325e9e'
    TEST_PREFIX_EXTRA1_HASH = '965f3c516d33a78869e22ac4150ff47ba2048aaabeaef5ece1fb9e645f9a0e7d'
    TEST_PREFIX_VARY_ON1_EXTRA1_HASH = '305be4c63ba1e877c3750cb72306cb28c6ee5530a768796de3138c01da655460'
    TEST_PREFIX_VARY_ON1_EXTRA2_HASH = '816d07e107886a0307f3dfc0785bf48b87acc146e53a1da0ac6cbd96d509e4cf'

    def test_get_cache_hash(self):
        self.assertEqual('', CacheAwareModel.get_cache_provider().get_hash([]))
        self.assertEqual('', CacheAwareModel.get_cache_provider().get_hash((i for i in [])))
        self.assertEqual(self.VARY_ON1_HASH, CacheAwareModel.get_cache_provider().get_hash(self.VARY_ON1))
        self.assertEqual(self.EXTRA1_HASH, CacheAwareModel.get_cache_provider().get_hash(self.EXTRA1))

    def test_get_key(self):
        self.assertEqual(self.TEST_PREFIX_HASH, CacheAwareModel.get_cache_provider().get_key(TEST_PREFIX))
        self.assertEqual(self.TEST_PREFIX_VARY_ON1_HASH, CacheAwareModel.get_cache_provider().get_key(
            TEST_PREFIX, vary_on=self.VARY_ON1))
        self.assertEqual(self.TEST_PREFIX_EXTRA1_HASH, CacheAwareModel.get_cache_provider().get_key(
            TEST_PREFIX, extra=self.EXTRA1))
        self.assertEqual(self.TEST_PREFIX_VARY_ON1_EXTRA1_HASH, CacheAwareModel.get_cache_provider().get_key(
            TEST_PREFIX, vary_on=self.VARY_ON1, extra=self.EXTRA1))
        self.assertEqual(self.TEST_PREFIX_VARY_ON1_EXTRA2_HASH, CacheAwareModel.get_cache_provider().get_key(
            TEST_PREFIX, vary_on=self.VARY_ON1, extra=self.EXTRA2))

    def test_get_extra_key(self):
        self.assertEqual(self.TEST_PREFIX_VARY_ON1_EXTRA_HASH, CacheAwareModel.get_cache_provider().get_extra_key(
            TEST_PREFIX, vary_on=self.VARY_ON1))

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
            self.TEST_PREFIX_VARY_ON1_EXTRA1_HASH,
            CacheAwareModel.get_cache_provider()._get_instance('default').get(self.TEST_PREFIX_VARY_ON1_EXTRA_HASH)
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
            f'{self.TEST_PREFIX_VARY_ON1_EXTRA1_HASH};{self.TEST_PREFIX_VARY_ON1_EXTRA2_HASH}',
            CacheAwareModel.get_cache_provider()._get_instance('default').get(
                self.TEST_PREFIX_VARY_ON1_EXTRA_HASH
            )
        )
        CacheAwareModel.get_cache_provider().set_data(
            TEST_PREFIX, self.TEST_INT, vary_on=self.VARY_ON1, extra=self.EXTRA2)
        self.assertEqual(
            f'{self.TEST_PREFIX_VARY_ON1_EXTRA1_HASH};{self.TEST_PREFIX_VARY_ON1_EXTRA2_HASH}',
            CacheAwareModel.get_cache_provider()._get_instance('default').get(
                self.TEST_PREFIX_VARY_ON1_EXTRA_HASH
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
