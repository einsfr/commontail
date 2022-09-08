import abc

from typing import Optional, List, Type, Iterable, Any

from django.conf import settings
from django.http import HttpRequest
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from wagtail.models import Page, Site

from .cache import AbstractCacheAwarePage, CacheMeta, CacheProvider
from .hierarchyonly import AbstractHierarchyOnlyPage


__all__ = ['STRUCTURED_DATA_CACHE_PREFIX', 'AbstractStructuredDataProvider',
           'HierarchyBreadcrumbsStructuredDataProvider', 'StructuredDataAware', 'AbstractStructuredDataAwarePage', ]


STRUCTURED_DATA_CACHE_PREFIX: str = 'structured_data'


class AbstractStructuredDataProvider(abc.ABC):

    template: Optional[str] = None

    @abc.abstractmethod
    def get_context(self, data_object: 'StructuredDataAware', request: HttpRequest) -> dict:
        raise NotImplementedError

    def get_template(self, data_object: 'StructuredDataAware', request: HttpRequest) -> Optional[str]:
        return self.template

    def render(self, data_object: 'StructuredDataAware', request: HttpRequest) -> str:
        return render_to_string(
            self.get_template(data_object, request),
            context=self.get_context(data_object, request)
        )


class HierarchyBreadcrumbsStructuredDataProvider(AbstractStructuredDataProvider):

    template: Optional[str] = 'commontail/structureddata/breadcrumbs.html'

    def get_context(self, data_object: Page, request: HttpRequest) -> dict:
        if not isinstance(data_object, Page):
            raise TypeError('Structured data provider HierarchyBreadcrumbsStructuredDataProvider may be used with'
                            'Page class successors only.')

        items: List[Page] = [
            item for item in data_object.get_ancestors(inclusive=True).filter(depth__gt=2).specific()
            if not isinstance(item, AbstractHierarchyOnlyPage)
        ]
        root_url: str = Site.find_for_request(request).root_url

        return {
            'items': items,
            'root_url': root_url,
        }


class StructuredDataAware:

    structured_data_providers: List[Type[AbstractStructuredDataProvider]] = []

    def get_structured_data(self, request: HttpRequest) -> str:
        return mark_safe(
            '\r\n'.join(
                [provider().render(self, request) for provider in self.structured_data_providers]
            )
        )


class AbstractStructuredDataAwarePage(StructuredDataAware, AbstractCacheAwarePage):

    class Meta:
        abstract = True

    cache_prefixes = AbstractCacheAwarePage.cache_prefixes + {
        STRUCTURED_DATA_CACHE_PREFIX: CacheMeta('default', settings.COMMONTAIL_STRUCTURED_DATA_CACHE_LIFETIME)
    }

    structured_data_providers = [HierarchyBreadcrumbsStructuredDataProvider, ]

    def get_cache_vary_on(self) -> Iterable[Any]:
        return self.pk,

    def get_structured_data(self, request: HttpRequest) -> str:
        cache_provider: CacheProvider = self.get_cache_provider()

        data: str = cache_provider.get_data(STRUCTURED_DATA_CACHE_PREFIX, self.get_cache_vary_on())

        if data is None:
            data = super().get_structured_data(request)
            cache_provider.set_data(STRUCTURED_DATA_CACHE_PREFIX, data, self.get_cache_vary_on())

        return data
