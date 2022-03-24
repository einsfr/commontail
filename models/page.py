from typing import List, Tuple, Union, Any, Type, Optional, Dict

from django.conf import settings
from django.core.paginator import Paginator, Page
from django.db import models

from wagtail.core.models import Page

from .opengraph import AbstractOpenGraphAwarePage
from .pagination import AbstractPaginationAwarePage, PaginatorPaginationData
from .seo import AbstractSEOAwarePage
from .structureddata import AbstractStructuredDataAwarePage


__all__ = ['AbstractBasePage', 'AbstractBaseIndexPage', 'AbstractContentStreamPage', ]


class AbstractBasePage(AbstractOpenGraphAwarePage, AbstractStructuredDataAwarePage, AbstractSEOAwarePage):

    class Meta:
        abstract = True

    cache_prefixes = AbstractOpenGraphAwarePage.cache_prefixes + AbstractStructuredDataAwarePage.cache_prefixes


class AbstractBaseIndexPage(AbstractPaginationAwarePage, AbstractBasePage):

    class Meta:
        abstract = True

    def get_items_class(self) -> Type[Page]:
        raise NotImplementedError

    def get_items_queryset(self) -> models.QuerySet:
        return self.get_items_class().objects.live().descendant_of(self).order_by(*self.get_items_queryset_order())

    def get_items_queryset_filters(self, request) -> Optional[Dict]:
        raise NotImplementedError

    def get_items_queryset_order(self) -> Union[Tuple, List]:
        items_meta_ordering: Union[Tuple[Any], List[Any]] = getattr(self.get_items_class().Meta, 'ordering', None)
        if items_meta_ordering:
            return items_meta_ordering

        return '-last_published_at', '-id'

    def get_per_page_number(self, request) -> int:
        raise NotImplementedError

    def get_context(self, request, *args, **kwargs):
        items_qs: models.QuerySet = self.get_items_queryset()
        filters: Optional[Dict] = self.get_items_queryset_filters(request)
        filtering_enabled: bool = bool(filters)

        if filtering_enabled:
            items_qs.filter(**filters)

        paginator: Paginator = Paginator(items_qs, self.get_per_page_number(request))
        items_page: Page = paginator.get_page(request.GET.get(settings.COMMONTAIL_PAGINATION_GET_KEY, 1))

        context: Dict = super().get_context(request, *args, **kwargs)
        context.update({
            'items': items_page,
            'filtering_enabled': filtering_enabled,
            'pagination_data': PaginatorPaginationData(paginator, items_page),
            'allow_robots_indexing': not filtering_enabled,
        })

        return context


class AbstractContentStreamPage(AbstractBasePage):

    class Meta:
        abstract = True
