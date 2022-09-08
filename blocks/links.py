from django.utils.translation import gettext_lazy as _

from wagtail import blocks
from wagtail.documents.blocks import DocumentChooserBlock


__all__ = ['AnchorLinkBlock', 'DocumentLinkBlock', 'ExternalLinkBlock', 'LinksBlock', 'LinkedMaterialsBlock',
           'PageLinkBlock', ]


class AnchorLinkBlock(blocks.StructBlock):

    class Meta:
        icon = 'link'
        label = _('On-page anchor link')
        template = 'commontail/blocks/link_anchor.html'

    anchor_id = blocks.CharBlock(required=True, max_length=64, label=_('Anchor\'s ID'))

    link_text = blocks.CharBlock(required=False, max_length=64, label=_('Link\'s text'))


class DocumentLinkBlock(blocks.StructBlock):

    class Meta:
        icon = 'link'
        label = _('Link to a document')
        template = 'commontail/blocks/link_document.html'

    document = DocumentChooserBlock(required=True, label=_('Document'))

    link_text = blocks.CharBlock(required=False, max_length=64, label=_('Link\'s text'))


class ExternalLinkBlock(blocks.StructBlock):

    class Meta:
        icon = 'link'
        label = _('External link')
        template = 'commontail/blocks/link_external.html'

    link_text = blocks.CharBlock(required=False, max_length=64, label=_('Link\'s text'))

    url = blocks.URLBlock(required=True, label=_('URL'))


class PageLinkBlock(blocks.StructBlock):

    class Meta:
        icon = 'link'
        label = _('Link to a page')
        template = 'commontail/blocks/link_page.html'

    link_text = blocks.CharBlock(required=False, max_length=64, label=_('Link\'s text'))

    page = blocks.PageChooserBlock(required=True, label=_('Page'))

    query_string = blocks.CharBlock(required=False, max_length=255, label=_('Query string'))


class LinksBlock(blocks.StreamBlock):

    class Meta:
        icon = 'link'
        label = _('Links')
        template = 'commontail/blocks/links.html'

    anchor = AnchorLinkBlock()

    document = DocumentLinkBlock()

    external = ExternalLinkBlock()

    page = PageLinkBlock()


class LinkedMaterialsBlock(blocks.StructBlock):

    class Meta:
        icon = 'link'
        label = _('Linked materials')
        template = 'commontail/blocks/linked_materials.html'

    caption = blocks.CharBlock(required=False, max_length=64, label=_('Heading'))

    links = LinksBlock()
