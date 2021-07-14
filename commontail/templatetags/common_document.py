from django import template
from django.conf import settings

from wagtail.documents.models import Document


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
