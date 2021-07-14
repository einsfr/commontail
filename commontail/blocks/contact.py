from django.conf import settings
from django.utils.translation import gettext_lazy as _lazy

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
        label = _lazy('Address')
        icon = 'fa-map-signs'
        template = 'commontail/blocks/address.html'

    address = blocks.CharBlock(max_length=255, label=_lazy('Address'))


class EmailBlock(blocks.StructBlock):

    class Meta:
        label = _lazy('E-mail')
        icon = 'fa-envelope-open-o'
        template = 'commontail/blocks/email.html'

    email = blocks.EmailBlock(label=_lazy('E-mail'))

    comment = blocks.CharBlock(max_length=32, label=_lazy('Comment'), required=False)


class FacebookBlock(SocialLinkMixin, blocks.StructBlock):

    class Meta:
        label = _lazy('Facebook')
        icon = 'fa-facebook'
        template = 'commontail/blocks/facebook.html'

    title = blocks.CharBlock(max_length=32, label=_lazy('Link\'s text'), required=False)

    url = blocks.URLBlock(label=_lazy('URL'))


class ICQBlock(blocks.StructBlock):

    class Meta:
        label = _lazy('ICQ')
        template = 'commontail/blocks/icq.html'

    number = blocks.CharBlock(max_length=12, label=_lazy('Number'))

    comment = blocks.CharBlock(max_length=32, label=_lazy('Comment'), required=False)


class InstagramBlock(SocialLinkMixin, blocks.StructBlock):

    class Meta:
        label = _lazy('Instagram')
        icon = 'fa-instagram'
        template = 'commontail/blocks/instagram.html'

    title = blocks.CharBlock(max_length=32, label=_lazy('Link\'s text'), required=False)

    url = blocks.URLBlock(label=_lazy('URL'))


class MapBlock(blocks.StructBlock):

    class Meta:
        label = _lazy('Map')
        icon = 'fa-map'
        template = 'commontail/blocks/map.html'

    title = blocks.CharBlock(max_length=32, label=_lazy('Heading'))

    code = blocks.RawHTMLBlock(label=_lazy('Map\'s HTML code'))


class OdnoklassnikiBlock(SocialLinkMixin, blocks.StructBlock):

    class Meta:
        label = _lazy('Odnoklassniki')
        icon = 'fa-odnoklassniki'
        template = 'commontail/blocks/odnoklassniki.html'

    title = blocks.CharBlock(max_length=32, label=_lazy('Link\'s text'), required=False)

    url = blocks.URLBlock(label=_lazy('URL'))


class PhoneBlock(blocks.StructBlock):

    class Meta:
        label = _lazy('Phone')
        icon = 'fa-phone'
        template = 'commontail/blocks/phone.html'

    number = blocks.CharBlock(max_length=32, label=_lazy('Number'))

    comment = blocks.CharBlock(max_length=32, label=_lazy('Comment'), required=False)


class FaxBlock(PhoneBlock):

    class Meta:
        label = _lazy('Fax')
        icon = 'fa-fax'
        template = 'commontail/blocks/fax.html'


class SkypeBlock(blocks.StructBlock):

    class Meta:
        label = _lazy('Skype')
        icon = 'fa-skype'
        template = 'commontail/blocks/skype.html'

    id = blocks.CharBlock(max_length=32, label=_lazy('ID'))

    comment = blocks.CharBlock(max_length=32, label=_lazy('Comment'), required=False)


class TelegramBlock(blocks.StructBlock):

    class Meta:
        label = _lazy('Telegram')
        icon = 'fa-telegram'
        template = 'commontail/blocks/telegram.html'

    title = blocks.CharBlock(max_length=32, label=_lazy('Link\'s text'), required=False)

    url = blocks.URLBlock(label=_lazy('URL'))


class TwitterBlock(SocialLinkMixin, blocks.StructBlock):

    class Meta:
        label = _lazy('Twitter')
        icon = 'fa-twitter'
        template = 'commontail/blocks/twitter.html'

    title = blocks.CharBlock(max_length=32, label=_lazy('Link\'s text'), required=False)

    url = blocks.URLBlock(label=_lazy('URL'))


class VKontakteBlock(SocialLinkMixin, blocks.StructBlock):

    class Meta:
        label = _lazy('VKontakte')
        icon = 'fa-vk'
        template = 'commontail/blocks/vkontakte.html'

    title = blocks.CharBlock(max_length=32, label=_lazy('Link\'s text'), required=False)

    url = blocks.URLBlock(label=_lazy('URL'))


class WhatsappBlock(blocks.StructBlock):

    class Meta:
        label = _lazy('Whatsapp')
        icon = 'fa-whatsapp'
        template = 'commontail/blocks/whatsapp.html'

    number = blocks.CharBlock(max_length=32, label=_lazy('Number'))

    comment = blocks.CharBlock(max_length=32, label=_lazy('Comment'))


class WorkHoursBlock(blocks.StructBlock):

    class Meta:
        label = _lazy('Work hours')
        icon = 'fa-clock-o'
        template = 'commontail/blocks/work_hours.html'

    work_hours = blocks.CharBlock(max_length=64, label=_lazy('Work hours'))


class YouTubeBlock(SocialLinkMixin, blocks.StructBlock):

    class Meta:
        label = _lazy('YouTube')
        icon = 'fa-youtube'
        template = 'commontail/blocks/youtube.html'

    title = blocks.CharBlock(max_length=32, label=_lazy('Link\'s text'), required=False)

    url = blocks.URLBlock(label=_lazy('URL'))


class ContactBlock(blocks.StreamBlock):

    class Meta:
        label = _lazy('Contacts')
        template = 'commontail/blocks/contact.html'

    SOCIAL_NETWORKS = ['facebook', 'instagram', 'odnoklassniki', 'telegram', 'twitter', 'vk', 'youtube']

    address = AddressBlock()

    address_post = AddressBlock(label=_lazy('Post address'))

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
