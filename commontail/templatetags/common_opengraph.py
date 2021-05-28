from typing import Dict, Any

from django import template
from django.utils.html import escape, mark_safe

from ..models import OpenGraphAware


register = template.Library()


@register.inclusion_tag('commontail/templatetags/opengraph.html', takes_context=True)
def opengraph(context: Dict, data_object: OpenGraphAware) -> Dict[str, Any]:
    if isinstance(data_object, OpenGraphAware):
        return {
            'data': data_object.get_opengraph_data(context['request'])
        }
    else:
        return {}


@register.simple_tag
def opengraph_head(data_object: OpenGraphAware) -> str:
    if isinstance(data_object, OpenGraphAware):
        prefix: str = escape(' '.join([f'{ns}: {url}' for ns, url in data_object.get_opengraph_namespaces()]))

        return mark_safe(f'prefix="{prefix}"')
    else:
        return ''
