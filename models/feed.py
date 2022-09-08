from typing import Optional, Type

from django.contrib.syndication.views import Feed
from django.utils.feedgenerator import Rss201rev2Feed

from wagtail.models import Page
from wagtail.templatetags.wagtailcore_tags import richtext


__all__ = ['RichTextDescriptionRss201rev2Feed', 'ChildPageFeed', 'AbstractFeedablePage', ]


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


class AbstractFeedablePage(Page):

    class Meta:
        abstract = True

    feed_class: Optional[Type[Feed]] = None

    def serve(self, request, *args, **kwargs):
        if request.method == 'GET' and 'rss' in request.GET:
            return self.feed_class()(request, self)
        else:
            return super().serve(request, *args, **kwargs)
