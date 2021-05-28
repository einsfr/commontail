from typing import Any

from django.db.models.signals import post_save
from django.core.cache import cache

from ..models import OpenGraphAware


__all__ = ['register_opengraph_signal_handlers', ]


def opengraph_post_save(sender, **kwargs):
    instance: Any = kwargs['instance']
    if isinstance(instance, OpenGraphAware):
        cache.delete(instance.get_opengraph_cache_key())


def register_opengraph_signal_handlers():
    post_save.connect(opengraph_post_save)
