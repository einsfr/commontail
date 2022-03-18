from django.db.models.signals import post_save, post_delete

from ..models import AbstractCacheAware


__all__ = ['register_cache_aware_signal_handlers', ]


def cache_aware_action(instance: AbstractCacheAware, action: str) -> None:
    policy: int = instance.CACHE_POLICIES[action]
    if policy == AbstractCacheAware.CACHE_ACTION_NONE:
        return
    elif policy == AbstractCacheAware.CACHE_ACTION_CLEAR:
        instance.clear_cache(instance.get_cache_vary_on())


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
