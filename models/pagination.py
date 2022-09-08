import abc

from typing import Dict

from django.conf import settings
from django.core.paginator import Paginator, Page as PaginatorPage
from django.http import HttpRequest, QueryDict
from django.utils.functional import lazy

from wagtail.models import Page


__all__ = ['AbstractPaginationData', 'PaginatorPaginationData', 'ParametricPaginationData',
           'AbstractPaginationAwarePage', ]


class AbstractPaginationData(abc.ABC):

    @property
    @abc.abstractmethod
    def has_next_page(self) -> bool:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def has_other_pages(self) -> bool:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def has_previous_page(self) -> bool:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def is_first_page(self) -> bool:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def items_count(self) -> int:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def number_of_pages(self) -> int:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def page_number(self) -> int:
        raise NotImplementedError


class PaginatorPaginationData(AbstractPaginationData):

    def __init__(self, paginator: Paginator, page: PaginatorPage):
        self._paginator: Paginator = paginator
        self._page: PaginatorPage = page

    @property
    def has_next_page(self) -> bool:
        return self._page.has_next()

    @property
    def has_other_pages(self) -> bool:
        return self._page.has_other_pages()

    @property
    def has_previous_page(self) -> bool:
        return self._page.has_previous()

    @property
    def is_first_page(self) -> bool:
        return self._page.number == 1

    @property
    def items_count(self) -> int:
        return self._paginator.count

    @property
    def number_of_pages(self) -> int:
        return self._paginator.num_pages

    @property
    def page_number(self) -> int:
        return self._page.number


class ParametricPaginationData(AbstractPaginationData):

    def __init__(self, page_number: int, number_of_pages: int, items_count: int):
        self._page_number: int = page_number
        self._number_of_pages: int = number_of_pages
        self._items_count: int = items_count

    @property
    def has_next_page(self) -> bool:
        return self._page_number < self._number_of_pages

    @property
    def has_other_pages(self) -> bool:
        return self.has_previous_page or self.has_next_page

    @property
    def has_previous_page(self) -> bool:
        return self._page_number > 1

    @property
    def is_first_page(self) -> bool:
        return self._page_number == 1

    @property
    def items_count(self) -> int:
        return self._items_count

    @property
    def number_of_pages(self) -> int:
        return self._number_of_pages

    @property
    def page_number(self) -> int:
        return self._page_number


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
        get_dict[settings.COMMONTAIL_PAGINATION_GET_KEY] = pagination_data.page_number + 1

        return f'{request.path}?{get_dict.urlencode()}'

    @staticmethod
    def get_link_rel_prev(request: HttpRequest, pagination_data: AbstractPaginationData) -> str:
        if not isinstance(pagination_data, AbstractPaginationData) or not pagination_data.has_previous_page:
            return ''

        get_dict: QueryDict = request.GET.copy()

        if pagination_data.page_number > 2:
            get_dict[settings.COMMONTAIL_PAGINATION_GET_KEY] = pagination_data.page_number - 1
        else:
            get_dict.pop(settings.COMMONTAIL_PAGINATION_GET_KEY, None)

        query_string: str = get_dict.urlencode()

        return f'{request.path}?{query_string}' if query_string else request.path
