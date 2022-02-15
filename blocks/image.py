from django.utils.translation import gettext_lazy as _lazy

from wagtail.core import blocks
from wagtail.images.blocks import ImageChooserBlock


__all__ = ['ImageBlock', 'ImageGalleryBlock', ]


class ImageBlock(blocks.StructBlock):

    class Meta:
        icon = 'image'
        label = _lazy('Image')
        template = 'commontail/blocks/image.html'

    IMAGE_WIDTH_SMALL = 150
    IMAGE_WIDTH_MEDIUM = 300
    IMAGE_WIDTH_LARGE = 450
    IMAGE_WIDTH_XLARGE = 600
    IMAGE_WIDTH_XXLARGE = 750

    align = blocks.ChoiceBlock(choices=[
        ('left', _lazy('Left')),
        ('center', _lazy('Center')),
        ('right', _lazy('Right')),
    ], default='left', required=True, label=_lazy('Align'))

    caption = blocks.CharBlock(max_length=128, required=False, label=_lazy('Caption'))

    hide_caption = blocks.BooleanBlock(required=False, label=_lazy('Hide caption'))

    image = ImageChooserBlock(required=True, label=_lazy('Image'))

    size = blocks.ChoiceBlock(choices=[
        ('small', _lazy('Small')),
        ('medium', _lazy('Medium')),
        ('large', _lazy('Large')),
        ('xlarge', _lazy('Very large')),
        ('xxlarge', _lazy('Extra large')),
    ], default='medium', required=True, label=_lazy('Size'))

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
        label = _lazy('Image gallery')
        template = 'commontail/blocks/gallery.html'

    images = blocks.ListBlock(ImageChooserBlock(label=_lazy('Image')), label=_lazy('Images'))

    title = blocks.CharBlock(max_length=128, required=False, label=_lazy('Heading'))
