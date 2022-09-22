from django.utils.translation import gettext_lazy as _

from wagtail.admin.panels import FieldPanel
from wagtail import blocks
from wagtail.fields import StreamField
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
                    ('title', blocks.CharBlock(max_length=64, label=_('Data set title'), required=False)),
                    ('contact_data', ContactBlock()),
                ],
                label=_('Contact data')
            ))
        ],
        blank=True,
        use_json_field=True,
        verbose_name=_('contacts'),
    )

    content_panels = [
        FieldPanel('contacts'),
    ]

    opengraph_provider = OpenGraphGlobalLogoImagePageProvider()

    search_fields = [
        index.SearchField('contacts', boost=1, partial_match=False),
    ]
