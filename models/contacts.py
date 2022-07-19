from django.utils.translation import gettext_lazy as _lazy

from wagtail.admin.edit_handlers import StreamFieldPanel
from wagtail.core import blocks
from wagtail.core.fields import StreamField
from wagtail.search import index

from ..blocks import ContactBlock

from .opengraph import OpenGraphGlobalLogoImagePageProvider
from .page import AbstractBasePage
from .singleton import AbstractPerSiteSingletonPage


__all__ = ['AbstractContactsPage', ]


class AbstractContactsPage(AbstractPerSiteSingletonPage, AbstractBasePage):

    class Meta:
        abstract = True

    contacts = StreamField(
        [
            ('contact', blocks.StructBlock(
                [
                    ('title', blocks.CharBlock(max_length=64, label=_lazy('Data set title'), required=False)),
                    ('contact_data', ContactBlock()),
                ],
                label=_lazy('Contact data')
            ))
        ],
        blank=True,
        verbose_name=_lazy('contacts'),
    )

    content_panels = AbstractBasePage.content_panels + [
        StreamFieldPanel('contacts'),
    ]

    opengraph_provider = OpenGraphGlobalLogoImagePageProvider()

    search_fields = AbstractBasePage.search_fields + [
        index.SearchField('contacts', boost=1, partial_match=False),
    ]
