from typing import Iterable, Any

from django.conf import settings
from django.utils.translation import gettext_lazy as _

from wagtail.admin.edit_handlers import FieldPanel

from .cache import AbstractCacheAware, CacheMeta
from .links import AbstractLinkFields
from .utils import AbstractSiteHandleModel


__all__ = ['NamedReference', ]


class NamedReference(AbstractCacheAware, AbstractLinkFields, AbstractSiteHandleModel):

    class Meta(AbstractSiteHandleModel.Meta):
        verbose_name = _('named reference')
        verbose_name_plural = _('named references')

    cache_template_prefix = 'named_reference_template'
    cache_prefixes = AbstractCacheAware.cache_prefixes + {
        cache_template_prefix: CacheMeta(
            ('template_fragments', 'default'),
            settings.COMMONTAIL_NAMED_URL_CACHE_LIFETIME
        )
    }

    panels = [
        FieldPanel('site'),
        FieldPanel('handle'),
    ] + AbstractLinkFields.panels

    def __str__(self):
        return f'{self.site}: {self.handle}'

    def get_cache_vary_on(self) -> Iterable[Any]:
        return self.site_id, self.handle
