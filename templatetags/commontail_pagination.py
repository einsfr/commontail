from typing import Dict, Any, Optional

from django import template
from django.conf import settings
from django.core.paginator import Page as PaginatorPage
from django.http.request import QueryDict

from ..models import AbstractPaginationData


register = template.Library()


def _prepare(number_of_pages: int, current_page_number: int, has_next_page: bool, has_prev_page: bool,
             query_dict: QueryDict) -> Dict[str, Any]:
    neighbours_count: int = settings.COMMONTAIL_PAGINATION_NEIGHBOURS_COUNT
    page_count: int = number_of_pages
    current_page: int = current_page_number

    query_string: str
    if query_dict:
        query_dict = query_dict.copy()
        query_dict.pop(settings.COMMONTAIL_PAGINATION_GET_KEY, None)
        query_string = query_dict.urlencode()
    else:
        query_string = ''

    result: Dict[str, Any] = {
        'prev': None,
        'first': None,
        'others_left': False,
        'pages_left': [],
        'active': current_page,
        'pages_right': [],
        'others_right': False,
        'last': None,
        'next': None,
        'query_string': query_string
    }

    if has_prev_page:
        result['prev'] = current_page - 1
        range_start: int = current_page - neighbours_count

        if range_start <= 0:
            range_start = 1

        if range_start > 1:
            result['first'] = 1

            if range_start == 3:
                range_start = 2
            elif range_start > 3:
                result['others_left'] = True

        for i in range(range_start, current_page):
            result['pages_left'].append(i)

    if has_next_page:
        result['next'] = current_page + 1
        range_end: int = current_page + neighbours_count

        if range_end > page_count:
            range_end = page_count

        end_distance: int = page_count - range_end
        if end_distance > 0:
            result['last'] = page_count

            if end_distance == 2:
                range_end += 1
            elif end_distance > 2:
                result['others_right'] = True

        for i in range(current_page + 1, range_end + 1):
            result['pages_right'].append(i)

    return result


@register.inclusion_tag('commontail/templatetags/pagination.html')
def pagination(page: Optional[PaginatorPage], query_dict: QueryDict = None) -> Dict[str, Any]:
    return {
        'p': _prepare(
            page.paginator.num_pages, page.number, page.has_next(), page.has_previous(), query_dict
        ) if page.paginator.num_pages > 1 else None,
        'page_get_key': settings.COMMONTAIL_PAGINATION_GET_KEY,
    }


@register.inclusion_tag('commontail/templatetags/pagination.html')
def pagination_data(data: Optional[AbstractPaginationData], query_dict: QueryDict = None) -> Dict[str, Any]:
    return {
        'p': _prepare(
            data.number_of_pages, data.page_number, data.has_next_page, data.has_previous_page, query_dict
        ) if data and data.number_of_pages > 1 else None,
        'page_get_key': settings.COMMONTAIL_PAGINATION_GET_KEY,
    }
