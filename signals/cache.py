from django.db.models.signals import post_save, post_delete

from ..models import AbstractCacheAware, CacheProvider


__all__ = ['register_cache_aware_signal_handlers', ]


def cache_aware_action(instance: AbstractCacheAware, action: str) -> None:
    cache_provider: CacheProvider = instance.get_cache_provider()

    policy: int = cache_provider.CACHE_POLICIES[action]
    if policy == cache_provider.CACHE_ACTION_NONE:
        return
    elif policy == cache_provider.CACHE_ACTION_CLEAR:
        instance.get_cache_provider().clear(instance.get_cache_vary_on())
        try:
            for dependent in instance.get_cache_dependents():
                dependent.get_cache_provider().clear(dependent.get_cache_vary_on())
        except TypeError:
            pass


def cache_aware_post_save(sender, **kwargs):
    instance = kwargs['instance']
    if isinstance(instance, AbstractCacheAware):
        cache_aware_action(instance, 'save')


def cache_aware_post_delete(sender, **kwargs):
    instance = kwargs['instance']
    if isinstance(instance, AbstractCacheAware):
        cache_aware_action(instance, 'delete')


def register_cache_aware_signal_handlers():
    post_save.connect(cache_aware_post_save)
    post_delete.connect(cache_aware_post_delete)
