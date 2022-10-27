import mimetypes

from typing import Optional, Type

from django.contrib.syndication.views import Feed
from django.utils.feedgenerator import Rss201rev2Feed, Enclosure

from wagtail.images.models import AbstractRendition
from wagtail.models import Page
from wagtail.templatetags.wagtailcore_tags import richtext

from .author import FormattedSignatureData
from .publication import AbstractPublicationPage


__all__ = ['RichTextDescriptionRss201rev2Feed', 'ChildPageFeed', 'PublicationIndexChildPageFeed',
           'AbstractFeedablePage']


class RichTextDescriptionRss201rev2Feed(Rss201rev2Feed):

    def add_item_elements(self, handler, item):
        description = item['description']
        item['description'] = None

        super().add_item_elements(handler, item)

        handler.startElement('description', {})
        handler._write(f'<![CDATA[{richtext(description)}]]>')
        handler.endElement('description')


class ChildPageFeed(Feed):

    feed_length: int = 20

    def feed_url(self, obj: Page):
        return f'{self.link(obj)}?rss'

    def get_object(self, request, *args, **kwargs):
        page = args[0]

        if isinstance(page, Page):
            return page
        else:
            return Page.objects.get(pk=page).specific

    def item_link(self, item):
        return item.url

    def item_pubdate(self, item):
        return item.first_published_at

    def item_title(self, item):
        return item.title

    def item_updateddate(self, item):
        return item.last_published_at

    def items(self, obj: Page):
        return obj.get_children().live().order_by('-first_published_at').specific()[:self.feed_length]

    def link(self, obj: Page):
        return obj.url

    def title(self, obj: Page):
        return obj.title


class PublicationIndexChildPageFeed(ChildPageFeed):

    def item_author_email(self, obj: AbstractPublicationPage):
        author: FormattedSignatureData = obj.get_signature_first_author()

        if author and author.title and author.email:
            return author.email

    def item_author_name(self, obj: AbstractPublicationPage):
        author: FormattedSignatureData = obj.get_signature_first_author()

        if author and author.title and author.email:
            return author.title

    def item_enclosures(self, item: AbstractPublicationPage):
        if not item.image_announce:
            return []

        image_rendition: AbstractRendition = item.image_announce.get_rendition('original')
        if not image_rendition:
            return []

        mime_type, encoding = mimetypes.guess_type(image_rendition.url)

        try:
            file_size = str(image_rendition.file.size)
        except FileNotFoundError:
            return []

        return [Enclosure(image_rendition.full_url, str(file_size),
                          mime_type if mime_type is not None else '')]


class AbstractFeedablePage(Page):

    class Meta:
        abstract = True

    feed_class: Optional[Type[Feed]] = None

    def serve(self, request, *args, **kwargs):
        if request.method == 'GET' and 'rss' in request.GET:
            return self.feed_class()(request, self)
        else:
            return super().serve(request, *args, **kwargs)
