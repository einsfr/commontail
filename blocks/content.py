from django.conf import settings
from django.core.exceptions import ValidationError
from django.forms.utils import ErrorList
from django.utils.translation import gettext as _, gettext_lazy as _lazy

from lxml.html.clean import Cleaner

from wagtail.core import blocks

from .embed import ExtendedEmbedBlock
from .image import ImageBlock, ImageGalleryBlock
from .links import LinkedMaterialsBlock


__all__ = ['ByTheWayBlock', 'ContentStreamBlock', 'DefinitionBlock', 'HeadingBlock', 'RawHTMLBlock', 'TermBlock',
           'QuoteBlock', ]


class ByTheWayBlock(blocks.StructBlock):

    class Meta:
        icon = 'fa-paragraph'
        label = _lazy('By the way')
        template = 'commontail/blocks/bytheway.html'

    body = blocks.RichTextBlock(
        label=_lazy('Body'),
        features=settings.COMMONTAIL_RTF_NO_IMAGE_EMBED_FEATURES,
        template='commontail/blocks/self.html'
    )


class DefinitionBlock(blocks.StructBlock):

    class Meta:
        label = _lazy('Definition')
        template = 'commontail/blocks/definition.html'

    title = blocks.CharBlock(max_length=128, label=_lazy('Heading'))

    description = blocks.RichTextBlock(
        label=_lazy('Description'),
        features=settings.COMMONTAIL_RTF_INLINE_FEATURES,
        template='commontail/blocks/self.html'
    )


class HeadingBlock(blocks.StructBlock):

    class Meta:
        label = _lazy('Heading')
        template = 'commontail/blocks/heading.html',
        icon = 'title'

    size = blocks.ChoiceBlock(choices=[
        ('h2', 'H2'),
        ('h3', 'H3'),
        ('h4', 'H4'),
    ], required=True, label=_lazy('Size'))

    text = blocks.CharBlock(required=True, label=_lazy('Text'))


class QuoteBlock(blocks.StructBlock):

    class Meta:
        icon = 'fa-quote-right'
        label = _lazy('Quote')
        template = 'commontail/blocks/quote.html'

    body = blocks.RichTextBlock(
        label=_lazy('Body'),
        features=settings.COMMONTAIL_RTF_INLINE_FEATURES,
        template='commontail/blocks/self.html'
    )

    caption = blocks.CharBlock(
        label=_lazy('Caption'),
        max_length=255,
        required=False,
    )

    is_page_owner_comment = blocks.BooleanBlock(
        required=False,
        label=_lazy('Author\'s comment'),
        help_text=_lazy('If checked, this quote will be marked as page author\'s comment.')
    )

    def clean(self, value):
        result = super().clean(value)
        errors = {}
        if value['caption'] and value['is_page_owner_comment']:
            errors['caption'] = ErrorList([
                _('If "Author\'s comment" is checked, "Caption" must be empty.')
            ])
        elif not value['caption'] and not value['is_page_owner_comment']:
            msg = _('"Caption" can\'t be empty while "Author\'s comment" not checked.')
            errors['caption'] = ErrorList([msg])
            errors['is_page_owner_comment'] = ErrorList([msg])
        if errors:
            raise ValidationError('Validation error in StructBlock', params=errors)

        return result


class RawHTMLBlock(blocks.RawHTMLBlock):

    class Meta:
        icon = 'fa-code'
        label = _lazy('HTML')
        template = 'commontail/blocks/raw_html.html'

    def clean(self, value):
        cleaner = Cleaner()

        return super().clean(cleaner.clean_html(value))


class TermBlock(blocks.StructBlock):

    class Meta:
        label = _lazy('Term')
        template = 'commontail/blocks/term.html'

    icon_name = blocks.CharBlock(max_length=32, required=False, label=_lazy('Fontawesome icon\'s name'))

    text = blocks.RichTextBlock(features=['bold', 'italic', 'link', 'document-link', 'ul', 'ol', ], label=_lazy('Text'))


class ContentStreamBlock(blocks.StreamBlock):

    class Meta:
        template = 'commontail/blocks/content_stream.html'

    bytheway = ByTheWayBlock()

    definition_list = blocks.ListBlock(
        DefinitionBlock(),
        icon='fa-list',
        template='commontail/blocks/definition_list.html',
        label=_lazy('Definitions list')
    )

    embed = ExtendedEmbedBlock()

    gallery = ImageGalleryBlock()

    heading = HeadingBlock()

    image = ImageBlock()

    links = LinkedMaterialsBlock()

    paragraph = blocks.RichTextBlock(
        icon='fa-paragraph',
        template='commontail/blocks/self.html',
        features=settings.COMMONTAIL_RTF_NO_IMAGE_EMBED_FEATURES,
        label=_lazy('Paragraph')
    )

    quote = QuoteBlock()

    raw_html = RawHTMLBlock()
