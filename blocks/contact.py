from django.conf import settings
from django.utils.translation import gettext_lazy as _

from wagtail.core import blocks


__all__ = ['AddressBlock', 'EmailBlock', 'FacebookBlock', 'ICQBlock', 'InstagramBlock', 'MapBlock',
           'OdnoklassnikiBlock', 'PhoneBlock', 'FaxBlock', 'SkypeBlock', 'TelegramBlock', 'TwitterBlock',
           'VKontakteBlock', 'WhatsappBlock', 'WorkHoursBlock', 'YouTubeBlock', 'ContactBlock', 'SocialLinkMixin', ]


class SocialLinkMixin:

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        context.update({
            'open_in_new_window': settings.COMMONTAIL_SOCIAL_LINKS_OPEN_IN_NEW_WINDOW,
        })

        return context


class AddressBlock(blocks.StructBlock):

    class Meta:
        label = _('Address')
        icon = 'mail'
        template = 'commontail/blocks/address.html'

    address = blocks.CharBlock(max_length=255, label=_('Address'))


class EmailBlock(blocks.StructBlock):

    class Meta:
        label = _('E-mail')
        icon = 'mail'
        template = 'commontail/blocks/email.html'

    email = blocks.EmailBlock(label=_('E-mail'))

    comment = blocks.CharBlock(max_length=32, label=_('Comment'), required=False)


class FacebookBlock(SocialLinkMixin, blocks.StructBlock):

    class Meta:
        label = _('Facebook')
        icon = 'site'
        template = 'commontail/blocks/facebook.html'

    title = blocks.CharBlock(max_length=32, label=_('Link\'s text'), required=False)

    url = blocks.URLBlock(label=_('URL'))


class ICQBlock(blocks.StructBlock):

    class Meta:
        label = _('ICQ')
        icon = 'site'
        template = 'commontail/blocks/icq.html'

    number = blocks.CharBlock(max_length=12, label=_('Number'))

    comment = blocks.CharBlock(max_length=32, label=_('Comment'), required=False)


class InstagramBlock(SocialLinkMixin, blocks.StructBlock):

    class Meta:
        label = _('Instagram')
        icon = 'site'
        template = 'commontail/blocks/instagram.html'

    title = blocks.CharBlock(max_length=32, label=_('Link\'s text'), required=False)

    url = blocks.URLBlock(label=_('URL'))


class MapBlock(blocks.StructBlock):

    class Meta:
        label = _('Map')
        icon = 'site'
        template = 'commontail/blocks/map.html'

    title = blocks.CharBlock(max_length=32, label=_('Heading'))

    code = blocks.RawHTMLBlock(label=_('Map\'s HTML code'))


class OdnoklassnikiBlock(SocialLinkMixin, blocks.StructBlock):

    class Meta:
        label = _('Odnoklassniki')
        icon = 'site'
        template = 'commontail/blocks/odnoklassniki.html'

    title = blocks.CharBlock(max_length=32, label=_('Link\'s text'), required=False)

    url = blocks.URLBlock(label=_('URL'))


class PhoneBlock(blocks.StructBlock):

    class Meta:
        label = _('Phone')
        icon = 'site'
        template = 'commontail/blocks/phone.html'

    number = blocks.CharBlock(max_length=32, label=_('Number'))

    comment = blocks.CharBlock(max_length=32, label=_('Comment'), required=False)


class FaxBlock(PhoneBlock):

    class Meta:
        label = _('Fax')
        icon = 'site'
        template = 'commontail/blocks/fax.html'


class SkypeBlock(blocks.StructBlock):

    class Meta:
        label = _('Skype')
        icon = 'site'
        template = 'commontail/blocks/skype.html'

    id = blocks.CharBlock(max_length=32, label=_('ID'))

    comment = blocks.CharBlock(max_length=32, label=_('Comment'), required=False)


class TelegramBlock(blocks.StructBlock):

    class Meta:
        label = _('Telegram')
        icon = 'site'
        template = 'commontail/blocks/telegram.html'

    title = blocks.CharBlock(max_length=32, label=_('Link\'s text'), required=False)

    url = blocks.URLBlock(label=_('URL'))


class TwitterBlock(SocialLinkMixin, blocks.StructBlock):

    class Meta:
        label = _('Twitter')
        icon = 'site'
        template = 'commontail/blocks/twitter.html'

    title = blocks.CharBlock(max_length=32, label=_('Link\'s text'), required=False)

    url = blocks.URLBlock(label=_('URL'))


class VKontakteBlock(SocialLinkMixin, blocks.StructBlock):

    class Meta:
        label = _('VKontakte')
        icon = 'site'
        template = 'commontail/blocks/vkontakte.html'

    title = blocks.CharBlock(max_length=32, label=_('Link\'s text'), required=False)

    url = blocks.URLBlock(label=_('URL'))


class WhatsappBlock(blocks.StructBlock):

    class Meta:
        label = _('Whatsapp')
        icon = 'site'
        template = 'commontail/blocks/whatsapp.html'

    number = blocks.CharBlock(max_length=32, label=_('Number'))

    comment = blocks.CharBlock(max_length=32, label=_('Comment'))


class WorkHoursBlock(blocks.StructBlock):

    class Meta:
        label = _('Work hours')
        icon = 'time'
        template = 'commontail/blocks/work_hours.html'

    work_hours = blocks.CharBlock(max_length=64, label=_('Work hours'))


class YouTubeBlock(SocialLinkMixin, blocks.StructBlock):

    class Meta:
        label = _('YouTube')
        icon = 'site'
        template = 'commontail/blocks/youtube.html'

    title = blocks.CharBlock(max_length=32, label=_('Link\'s text'), required=False)

    url = blocks.URLBlock(label=_('URL'))


class ContactBlock(blocks.StreamBlock):

    class Meta:
        label = _('Contacts')
        icon = 'mail'
        template = 'commontail/blocks/contact.html'

    SOCIAL_NETWORKS = ['facebook', 'instagram', 'odnoklassniki', 'telegram', 'twitter', 'vk', 'youtube']

    address = AddressBlock()

    address_post = AddressBlock(label=_('Post address'))

    work_hours = WorkHoursBlock()

    phone = PhoneBlock()

    fax = FaxBlock()

    email = EmailBlock()

    icq = ICQBlock()

    skype = SkypeBlock()

    whatsapp = WhatsappBlock()

    map = MapBlock()

    facebook = FacebookBlock()

    instagram = InstagramBlock()

    odnoklassniki = OdnoklassnikiBlock()

    telegram = TelegramBlock()

    twitter = TwitterBlock()

    vk = VKontakteBlock()

    youtube = YouTubeBlock()

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        result = {
            'social_networks': []
        }
        for block in value:
            try:
                result[block.block_type].append(block)
            except KeyError:
                result[block.block_type] = [block]
            if block.block_type in self.SOCIAL_NETWORKS:
                result['social_networks'].append(block)
        context.update(result)

        return context
