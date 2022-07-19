from typing import Optional

from django import template
from django.template.loader import render_to_string

from ..models import AbstractAuthorSignaturePage, FormattedSignatureData


register = template.Library()


@register.simple_tag(takes_context=True)
def author(context: dict, page: AbstractAuthorSignaturePage) -> str:
    if not isinstance(page, AbstractAuthorSignaturePage):
        return ''

    first_author: Optional[FormattedSignatureData] = page.get_signature_first_author(context['request'])

    return render_to_string('commontail/templatetags/author.html', {
        'data': [first_author, ] if first_author else [],
    })


@register.simple_tag(takes_context=True)
def allauthors(context: dict, page: AbstractAuthorSignaturePage) -> str:
    if not isinstance(page, AbstractAuthorSignaturePage):
        return ''

    return render_to_string('commontail/templatetags/author.html', {
        'data': page.get_signature_data(context['request']),
    })
