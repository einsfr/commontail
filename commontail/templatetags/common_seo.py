from typing import Union, Optional

from django import template
from django.utils.translation import gettext_lazy as _

from wagtail.core.models import Page

from ..models import AbstractSEOAwarePage, AbstractPaginationData, AbstractPaginationAwarePage, SubstitutePage


register = template.Library()


@register.inclusion_tag('commontail/templatetags/metadescription.html', takes_context=True)
def metadescription(context: dict, page: Optional[Union[AbstractSEOAwarePage, Page, SubstitutePage]]):
    if not page:  # for 404-pages
        return {
            'text': '',
        }

    text: str
    if isinstance(page, Page):
        text = page.search_description

        if not text and isinstance(page, AbstractSEOAwarePage):
            text = page.seo_auto_meta_description
    elif isinstance(page, SubstitutePage):
        text = page.search_description
    else:
        raise template.exceptions.TemplateSyntaxError(
            f'metadescription tag takes only an instance of the one of following classes: '
            f'wagtail.core.models.Page, commontail.models.AbstractSEOAwarePage, commontail.models.SubstitutePage, '
            f'"{type(page)}" given.'
        )

    if isinstance(page, AbstractPaginationAwarePage):
        pagination_data: AbstractPaginationData = context.get('pagination_data')
        if text and pagination_data and not pagination_data.is_first_page:
            text = f'{text} ({_("page")} {pagination_data.page_number})'

    return {
        'text': text,
    }
