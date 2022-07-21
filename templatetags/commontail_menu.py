from typing import Optional

from django import template
from django.conf import settings
from django.template.loader import select_template

from wagtail.core.models import Site

from ..models import Menu
from ..utils.templatetags import HandleRenderedNode


register = template.Library()


@register.tag
def build_menu(parser, token):
    tag_name: str
    handle: str
    template_name: Optional[str]
    try:
        tag_name, handle, template_name = token.split_contents()
    except ValueError:
        template_name = None
        try:
            tag_name, handle = token.split_contents()
        except ValueError:
            raise template.TemplateSyntaxError(
                f'{token.contents.split()[0]} tag takes one required argument - menu handle - and one optional - '
                f'template name.'
            )

    return HandleRenderedNode(Menu, 'commontail/menu/menu', handle, template_name)
