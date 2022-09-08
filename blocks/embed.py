from django.utils.translation import gettext_lazy as _

from wagtail import blocks
from wagtail.embeds.blocks import EmbedBlock


__all__ = ['ExtendedEmbedBlock', ]


class ExtendedEmbedBlock(blocks.StructBlock):

    class Meta:
        icon = 'media'
        label = _('Embed')
        template = 'commontail/blocks/embed.html'

    align = blocks.ChoiceBlock(choices=[
        ('left', _('Left')),
        ('center', _('Center')),
        ('right', _('Right')),
    ], default='left', required=True, label=_('Align'))

    caption = blocks.CharBlock(max_length=128, required=False, label=_('Caption'))

    embed = EmbedBlock(label=_('Embed URL'))

    size = blocks.ChoiceBlock(choices=[
        ('small', _('Small')),
        ('medium', _('Medium')),
        ('large', _('Large')),
        ('xlarge', _('Very large')),
        ('xxlarge', _('Extra large')),
        ('full', _('Container\'s full width')),
    ], default='medium', required=True, label=_('Size'))
