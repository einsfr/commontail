from django import template
from django.conf import settings
from django.core.cache import cache
from django.template.defaultfilters import stringfilter

from wagtail.core.models import Page
from wagtail.core.rich_text.rewriters import FIND_A_TAG
from wagtail.documents.models import Document

from ..models import AbstractIconAware, AbstractExtendedTitleAware, NamedReference


register = template.Library()


@register.inclusion_tag('commontail/templatetags/document_link.html')
def document_link(document):
    if not isinstance(document, Document):
        raise template.TemplateSyntaxError('doclink tag accepts as its argument only an instance of the '
                                           '"wagtail.documents.models.Document" class.')
    return {
        'text': document.title,
        'url': document.url,
        # TODO: different icons may appear according to the document type - default only by now
        'icon': settings.COMMONTAIL_LINK_ICON_DOCUMENT_DEFAULT,
    }


@register.inclusion_tag('commontail/templatetags/external_link.html')
def external_link(title, url):
    return {
        'text': title if title else url,
        'url': url,
        'icon': settings.COMMONTAIL_LINK_ICON_EXTERNAL,
    }


@register.filter(is_safe=True)
@stringfilter
def link_target_blank(value: str):

    def replace_link(match):
        return '<a {} target="_blank">'.format(match.group(1))

    return FIND_A_TAG.sub(replace_link, value)


@register.simple_tag(takes_context=True)
def namedurl(context: dict, handle: str):
    site = context['request'].site
    cache_key = f'{settings.COMMONTAIL_NAMED_URL_CACHE_KEY_PREFIX}{site.pk}_{handle}'
    url = cache.get(cache_key)
    if url is None:
        try:
            nr = NamedReference.objects.get(site=site, handle=handle)
        except NamedReference.DoesNotExist as e:
            if settings.COMMONTAIL_NAMED_URL_SUPPRESS_NOT_FOUND_EXCEPTION:
                url = '#'
            else:
                raise e
        else:
            url = nr.url
            cache.set(cache_key, nr.url, settings.COMMONTAIL_NAMED_URL_CACHE_LIFETIME)

    return url


@register.inclusion_tag('commontail/templatetags/page_link.html')
def page_link(page: Page, forced_title=None, query_string=None):
    if not page.live:
        return {}

    page = page.specific
    if forced_title:
        text = forced_title
    else:
        text = page.get_link_title() if isinstance(page, AbstractExtendedTitleAware) else page.title

    return {
        'text': text,
        'url': f'{page.url}?{query_string}' if query_string else page.url,
        'icon': page.get_icon() if isinstance(page, AbstractIconAware) else None,
    }
