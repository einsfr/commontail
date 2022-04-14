from django import template
from django.template.defaultfilters import stringfilter

from ..utils.text import ru_plural


register = template.Library()


@register.filter(is_safe=False)
@stringfilter
def ruplural(value, arg):
    variants = arg.split(',')
    try:
        int_value = int(value)
    except ValueError:
        int_value = 0

    return f'{int_value} {ru_plural(int_value, variants)}'
