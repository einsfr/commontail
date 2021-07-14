from django.utils.translation import gettext_lazy as _lazy

from wagtail.core import blocks
from wagtail.documents.blocks import DocumentChooserBlock


__all__ = ['AnchorLinkBlock', 'DocumentLinkBlock', 'ExternalLinkBlock', 'LinksBlock', 'LinkedMaterialsBlock',
           'PageLinkBlock', ]


class AnchorLinkBlock(blocks.StructBlock):

    class Meta:
        icon = 'fa-link'
        label = _lazy('On-page anchor link')
        template = 'commontail/blocks/link_anchor.html'

    anchor_id = blocks.CharBlock(required=True, max_length=64, label=_lazy('Anchor\'s ID'))

    link_text = blocks.CharBlock(required=False, max_length=64, label=_lazy('Link\'s text'))


class DocumentLinkBlock(blocks.StructBlock):

    class Meta:
        icon = 'fa-link'
        label = _lazy('Link to a document')
        template = 'commontail/blocks/link_document.html'

    document = DocumentChooserBlock(required=True, label=_lazy('Document'))

    link_text = blocks.CharBlock(required=False, max_length=64, label=_lazy('Link\'s text'))


class ExternalLinkBlock(blocks.StructBlock):

    class Meta:
        icon = 'fa-link'
        label = _lazy('External link')
        template = 'commontail/blocks/link_external.html'

    link_text = blocks.CharBlock(required=False, max_length=64, label=_lazy('Link\'s text'))

    url = blocks.URLBlock(required=True, label=_lazy('URL'))


class PageLinkBlock(blocks.StructBlock):

    class Meta:
        icon = 'fa-link'
        label = _lazy('Link to a page')
        template = 'commontail/blocks/link_page.html'

    link_text = blocks.CharBlock(required=False, max_length=64, label=_lazy('Link\'s text'))

    page = blocks.PageChooserBlock(required=True, label=_lazy('Page'))

    query_string = blocks.CharBlock(required=False, max_length=255, label=_lazy('Query string'))


class LinksBlock(blocks.StreamBlock):

    class Meta:
        icon = 'fa-link'
        label = _lazy('Links')
        template = 'commontail/blocks/links.html'

    anchor = AnchorLinkBlock()

    document = DocumentLinkBlock()

    external = ExternalLinkBlock()

    page = PageLinkBlock()


class LinkedMaterialsBlock(blocks.StructBlock):

    class Meta:
        icon = 'fa-link'
        label = _lazy('Linked materials')
        template = 'commontail/blocks/linked_materials.html'

    caption = blocks.CharBlock(required=False, max_length=64, label=_lazy('Heading'))

    links = LinksBlock()
