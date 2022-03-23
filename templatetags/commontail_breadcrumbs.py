from typing import Union

from django import template
from django.conf import settings

from wagtail.core.models import Page

from ..models import SubstitutePage


register = template.Library()


@register.inclusion_tag('commontail/templatetags/breadcrumbs.html')
def breadcrumbs(page: Union[Page, SubstitutePage]):
    if isinstance(page, Page) or isinstance(page, SubstitutePage):
        return {
            'pages': page.get_ancestors(inclusive=True),
            'cache_vary_on': page.pk if isinstance(page, Page) else None,
            'cache_lifetime': settings.COMMONTAIL_BREADCRUMBS_CACHE_LIFETIME,
        }
    else:
        raise template.exceptions.TemplateSyntaxError(
            f'breadcrumbs tag accepts as its argument only an instance of one of following classes: '
            f'wagtail.core.models.Page, commontail.models.SubstitutePage, "{type(page)}" given.'
        )
