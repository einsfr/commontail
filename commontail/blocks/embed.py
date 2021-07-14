from django.utils.translation import gettext_lazy as _lazy

from wagtail.core import blocks
from wagtail.embeds.blocks import EmbedBlock


__all__ = ['ExtendedEmbedBlock', ]


class ExtendedEmbedBlock(blocks.StructBlock):

    class Meta:
        icon = 'fa-tv'
        label = _lazy('Embed')
        template = 'commontail/blocks/embed.html'

    align = blocks.ChoiceBlock(choices=[
        ('left', _lazy('Left')),
        ('center', _lazy('Center')),
        ('right', _lazy('Right')),
    ], default='left', required=True, label=_lazy('Align'))

    caption = blocks.CharBlock(max_length=128, required=False, label=_lazy('Caption'))

    embed = EmbedBlock(label=_lazy('Embed URL'))

    size = blocks.ChoiceBlock(choices=[
        ('small', _lazy('Small')),
        ('medium', _lazy('Medium')),
        ('large', _lazy('Large')),
        ('xlarge', _lazy('Very large')),
        ('xxlarge', _lazy('Extra large')),
        ('full', _lazy('Container\'s full width')),
    ], default='medium', required=True, label=_lazy('Size'))
