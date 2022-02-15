from django import template
from django.utils.safestring import mark_safe

from ..models import StructuredDataAware


register = template.Library()


@register.simple_tag(takes_context=True)
def structureddata(context, obj):
    if not isinstance(obj, StructuredDataAware):
        return ''

    return obj.get_structured_data(context['request'])


@register.filter
def jsonldvalue(value: str):
    return mark_safe(value.replace('\\', '\\\\').replace('"', '\\"').replace('</', '<\\/').replace('<!--', '<\\!--'))
