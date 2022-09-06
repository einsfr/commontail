import importlib
import re

from collections import OrderedDict, ValuesView
from typing import List, Tuple, Union, Any, Type, Optional, Dict

from django.conf import settings
from django.core.paginator import Paginator, Page
from django.db import models
from django.utils.translation import gettext_lazy as _

from wagtail.admin.edit_handlers import StreamFieldPanel
from wagtail.admin.forms import WagtailAdminPageForm
from wagtail.core.models import Page
from wagtail.core.fields import StreamField
from wagtail.search import index

from .opengraph import AbstractOpenGraphAwarePage
from .pagination import AbstractPaginationAwarePage, PaginatorPaginationData
from .seo import AbstractSEOAwarePage
from .structureddata import AbstractStructuredDataAwarePage


__all__ = ['AbstractBasePageForm', 'AbstractBasePage', 'AbstractBaseIndexPage', 'AbstractContentStreamPage',
           'get_content_stream_page_body_block', ]


def get_content_stream_page_body_block(**kwargs):
    import_parts: List[str] = settings.COMMONTAIL_CONTENT_STREAM_PAGE_BODY_BLOCK.split('.')
    module_name: str = '.'.join(import_parts[:-1])
    body_block = getattr(importlib.import_module(module_name), import_parts[-1])

    return body_block(**kwargs)


class AbstractBasePageForm(WagtailAdminPageForm):

    trailing_dots_re: re.Pattern = re.compile(r'([^.])\.$')
    multiple_spaces_re: re.Pattern = re.compile(r' {2,}')

    def remove_trailing_dots(self, cleaned_data: dict, field_names: Union[str, List[str]]) -> None:
        if not settings.COMMONTAIL_REMOVE_TRAILING_DOTS:
            return

        if type(field_names) == str:
            field_names = [field_names]

        for name in field_names:
            cleaned_data[name] = re.sub(self.trailing_dots_re, r'\1', cleaned_data[name])

    def remove_multiple_spaces(self, cleaned_data: dict, field_names: Union[str, List[str]]) -> None:
        if not settings.COMMONTAIL_REMOVE_MULTIPLE_SPACES:
            return

        if type(field_names) == str:
            field_names = [field_names]

        for name in field_names:
            cleaned_data[name] = re.sub(self.multiple_spaces_re, ' ', cleaned_data[name])

    def clean(self):
        cleaned_data = super().clean()

        self.remove_trailing_dots(cleaned_data, 'title')
        self.remove_multiple_spaces(cleaned_data, 'title')

        return cleaned_data


class AbstractBasePage(AbstractOpenGraphAwarePage, AbstractStructuredDataAwarePage, AbstractSEOAwarePage):

    class Meta:
        abstract = True

    base_form_class = AbstractBasePageForm

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

        return '-first_published_at', '-id'

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

    body = StreamField(
        get_content_stream_page_body_block(required=False),
        blank=True,
        verbose_name=_('page body'),
    )

    content_panels = [
        StreamFieldPanel('body'),
    ]

    include_toc: bool = False

    search_fields = AbstractBasePage.search_fields + [
        index.SearchField('body', boost=1, partial_match=False),
    ]

    def build_table_of_contents(self) -> Tuple[ValuesView, dict]:
        toc: OrderedDict = OrderedDict()
        headings: dict = dict()
        parent_h2: Optional[int] = None
        parent_h3: Optional[int] = None
        hid: int = 1

        for hblock in [
            block for block in self.body
            if block.block_type == 'heading' and block.value['size'] in ['h2', 'h3', 'h4']
        ]:
            if hblock.value['size'] == 'h2':
                toc[hid] = (hid, hblock, [])
                headings[hblock.id] = hid
                parent_h2 = hid
                hid += 1
            elif hblock.value['size'] == 'h3':
                if not parent_h2:
                    toc[hid] = (hid, None, [])
                    parent_h2 = hid
                    hid += 1
                toc[parent_h2][2].append((hid, hblock, []))
                headings[hblock.id] = hid
                parent_h3 = hid
                hid += 1
            else:
                if not parent_h3:
                    if not parent_h2:
                        toc[hid] = (hid, None, [])
                        parent_h2 = hid
                        hid += 1
                    toc[parent_h2][2].append((hid, None, []))
                    parent_h3 = hid
                    hid += 1
                for h3 in toc[parent_h2][2]:
                    if h3[0] == parent_h3:
                        h3[2].append((hid, hblock, []))
                        headings[hblock.id] = hid
                        hid += 1

                        break

        return toc.values(), headings

    def get_context(self, request, *args, **kwargs):
        if self.include_toc:
            toc, headings = self.build_table_of_contents()
        else:
            toc = None
            headings = None

        context = super().get_context(request, *args, **kwargs)
        context.update({
            'table_of_contents': toc,
            'headings': headings,
        })

        return context


