"""
Usage example:

from django.db import models

from modelcluster.fields import ParentalKey

from commontail.models import AbstractGlossaryPage, AbstractGlossaryItem

class SiteGlossaryPage(AbstractGlossaryPage):

    class Meta(AbstractGlossaryPage.Meta):
        pass

class SiteGlossaryItem(AbstractGlossaryItem):

    class Meta(AbstractGlossaryItem.Meta):
        pass

    glossary = ParentalKey(
        SiteGlossaryPage,
        on_delete=models.CASCADE,
        verbose_name='glossary',
        related_name='items',
    )
"""
import itertools
import functools

from django.conf import settings
from django.db import models
from django.db.models.functions import Left
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from wagtail.admin.edit_handlers import FieldPanel, StreamFieldPanel, RichTextFieldPanel, InlinePanel
from wagtail.core.fields import RichTextField, StreamField
from wagtail.search import index

from ..blocks import LinksBlock

from .opengraph import OpenGraphGlobalLogoImagePageProvider
from .page import AbstractBasePage


__all__ = ['AbstractGlossaryItem', 'AbstractGlossaryPage', ]


class AbstractGlossaryPage(AbstractBasePage):

    class Meta:
        abstract = True

    content_panels = AbstractBasePage.content_panels + [
        InlinePanel('items', label=_('Definitions'))
    ]

    items_attribute: str = 'items'

    opengraph_provider = OpenGraphGlobalLogoImagePageProvider()

    search_fields = AbstractBasePage.search_fields + [
        index.SearchField('get_items_search_terms', partial_match=False, boost=1.25),
        index.SearchField('get_items_search_descriptions', partial_match=False, boost=0.75),
    ]

    def get_items_search_terms(self) -> str:
        return '\r\n'.join((i.term for i in getattr(self, self.items_attribute).all()))

    def get_items_search_descriptions(self) -> str:
        return '\r\n'.join((i.description for i in getattr(self, self.items_attribute).all()))

    @cached_property
    def first_letters(self) -> list[str]:
        return list(
            getattr(self, self.items_attribute).all().annotate(first_letter=Left('term', 1)).distinct().order_by(
                'first_letter').values_list('first_letter', flat=True)
        )

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context['counter'] = functools.partial(next, itertools.count())

        return context


class AbstractGlossaryItem(models.Model):

    class Meta:
        ordering = ('term', )
        abstract = True

    description = RichTextField(
        blank=True,
        features=settings.COMMONTAIL_RTF_LIMITED_FEATURES,
        max_length=1000,
        verbose_name=_('description'),
    )

    links = StreamField(
        LinksBlock,
        blank=True,
        verbose_name=_('additional links'),
    )

    term = models.CharField(
        db_index=True,
        max_length=255,
        verbose_name=_('term'),
    )

    panels = [
        FieldPanel('term'),
        RichTextFieldPanel('description'),
        StreamFieldPanel('links'),
    ]

    def __str__(self):
        return self.term
