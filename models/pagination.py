import abc

from typing import Dict

from django.conf import settings
from django.core.paginator import Paginator, Page as PaginatorPage
from django.http import HttpRequest, QueryDict
from django.utils.functional import lazy

from wagtail.core.models import Page


__all__ = ['AbstractPaginationData', 'PaginatorPaginationData', 'ParametricPaginationData',
           'AbstractPaginationAwarePage', ]


class AbstractPaginationData(abc.ABC):

    @abc.abstractmethod
    def _get_is_first_page(self) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def _get_page_number(self) -> int:
        raise NotImplementedError

    @abc.abstractmethod
    def _get_has_next_page(self) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def _get_has_previous_page(self) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def _get_has_other_pages(self) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def _get_items_count(self) -> int:
        raise NotImplementedError

    @abc.abstractmethod
    def _get_number_of_pages(self) -> int:
        raise NotImplementedError

    has_next_page: bool = property(_get_has_next_page)

    has_other_pages: bool = property(_get_has_other_pages)

    has_previous_page: bool = property(_get_has_previous_page)

    is_first_page: bool = property(_get_is_first_page)

    items_count: int = property(_get_items_count)

    number_of_pages: int = property(_get_number_of_pages)

    page_number: int = property(_get_page_number)


class PaginatorPaginationData(AbstractPaginationData):

    def __init__(self, paginator: Paginator, page: PaginatorPage):
        self._paginator: Paginator = paginator
        self._page: PaginatorPage = page

    def _get_is_first_page(self) -> bool:
        return self._page.number == 1

    def _get_page_number(self) -> int:
        return self._page.number

    def _get_has_next_page(self) -> bool:
        return self._page.has_next()

    def _get_has_previous_page(self) -> bool:
        return self._page.has_previous()

    def _get_has_other_pages(self) -> bool:
        return self._page.has_other_pages()

    def _get_items_count(self) -> int:
        return self._paginator.count

    def _get_number_of_pages(self) -> int:
        return self._paginator.num_pages


class ParametricPaginationData(AbstractPaginationData):

    def __init__(self, page_number: int, number_of_pages: int, items_count: int):
        self._page_number: int = page_number
        self._number_of_pages: int = number_of_pages
        self._items_count: int = items_count

    def _get_is_first_page(self) -> bool:
        return self._page_number == 1

    def _get_page_number(self) -> int:
        return self._page_number

    def _get_has_next_page(self) -> bool:
        return self._page_number < self._number_of_pages

    def _get_has_previous_page(self) -> bool:
        return self._page_number > 1

    def _get_has_other_pages(self) -> bool:
        return self.has_previous_page or self.has_next_page

    def _get_items_count(self) -> int:
        return self._items_count

    def _get_number_of_pages(self) -> int:
        return self._number_of_pages


class AbstractPaginationAwarePage(Page):

    class Meta:
        abstract = True

    def get_context(self, request, *args, **kwargs):
        context: Dict = super().get_context(request, *args, **kwargs)
        context.update({
            'pagination_data': None,
            'link_rel_next': lazy(lambda: self.get_link_rel_next(request, context.get('pagination_data', None)), str),
            'link_rel_prev': lazy(lambda: self.get_link_rel_prev(request, context.get('pagination_data', None)), str),
        })

        return context

    @staticmethod
    def get_link_rel_next(request: HttpRequest, pagination_data: AbstractPaginationData) -> str:
        if not isinstance(pagination_data, AbstractPaginationData) or not pagination_data.has_next_page:
            return ''

        get_dict: QueryDict = request.GET.copy()
        get_dict[settings.PAGE_GET_KEY] = pagination_data.page_number + 1

        return f'{request.path}?{get_dict.urlencode()}'

    @staticmethod
    def get_link_rel_prev(request: HttpRequest, pagination_data: AbstractPaginationData) -> str:
        if not isinstance(pagination_data, AbstractPaginationData) or not pagination_data.has_previous_page:
            return ''

        get_dict: QueryDict = request.GET.copy()

        if pagination_data.page_number > 2:
            get_dict[settings.PAGE_GET_KEY] = pagination_data.page_number - 1
        else:
            get_dict.pop(settings.PAGE_GET_KEY, None)

        query_string: str = get_dict.urlencode()

        return f'{request.path}?{query_string}' if query_string else request.path
