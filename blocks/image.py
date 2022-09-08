from django.utils.translation import gettext_lazy as _

from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock


__all__ = ['ImageBlock', 'ImageGalleryBlock', ]


class ImageBlock(blocks.StructBlock):

    class Meta:
        icon = 'image'
        label = _('Image')
        template = 'commontail/blocks/image.html'

    IMAGE_WIDTH_SMALL = 150
    IMAGE_WIDTH_MEDIUM = 300
    IMAGE_WIDTH_LARGE = 450
    IMAGE_WIDTH_XLARGE = 600
    IMAGE_WIDTH_XXLARGE = 750

    align = blocks.ChoiceBlock(choices=[
        ('left', _('Left')),
        ('center', _('Center')),
        ('right', _('Right')),
    ], default='left', required=True, label=_('Align'))

    caption = blocks.CharBlock(max_length=128, required=False, label=_('Caption'))

    hide_caption = blocks.BooleanBlock(required=False, label=_('Hide caption'))

    image = ImageChooserBlock(required=True, label=_('Image'))

    size = blocks.ChoiceBlock(choices=[
        ('small', _('Small')),
        ('medium', _('Medium')),
        ('large', _('Large')),
        ('xlarge', _('Very large')),
        ('xxlarge', _('Extra large')),
    ], default='medium', required=True, label=_('Size'))

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        context.update({
            'allow_fullsize_view': value['image'].width > getattr(self, 'IMAGE_WIDTH_{}'.format(
                value['size'].upper()
            )),
            'size': value['size']
        })

        return context


class ImageGalleryBlock(blocks.StructBlock):

    class Meta:
        icon = 'image'
        label = _('Image gallery')
        template = 'commontail/blocks/gallery.html'

    images = blocks.ListBlock(ImageChooserBlock(label=_('Image')), label=_('Images'))

    title = blocks.CharBlock(max_length=128, required=False, label=_('Heading'))
