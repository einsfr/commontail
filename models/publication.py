from typing import Optional, Dict, Type

from django.db import models
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from wagtail.admin.edit_handlers import FieldPanel
from wagtail.core.models import Site, Page, PageManager, PageQuerySet
from wagtail.images.models import AbstractRendition

from .author import AbstractAuthorSignaturePage, FormattedSignatureData
from .counter import AbstractViewsCountablePage
from .page import AbstractContentStreamPage, AbstractBaseIndexPage, AbstractImageAnnounceSummaryPage
from .settings import get_logo_rendition
from .structureddata import AbstractStructuredDataProvider


__all__ = ['AbstractPublicationPage', 'AbstractPublicationIndexPage', 'PublicationStructuredDataProvider', ]


class PublicationStructuredDataProvider(AbstractStructuredDataProvider):

    template = 'commontail/structureddata/publication.html'

    def get_context(self, data_object: 'AbstractPublicationPage', request: HttpRequest) -> dict:
        if not isinstance(data_object, AbstractPublicationPage):
            raise TypeError(f'Structured data provider '
                            f'commontail.models.PublicationStructuredDataProvider may only be used '
                            f'with subclasses of commontail.models.AbstractPublicationPage.')

        site: Site = Site.find_for_request(request)
        logo_rendition: Optional[AbstractRendition] = get_logo_rendition(site=site)
        logo_url: Optional[str] = logo_rendition.url if logo_rendition else None

        author_data: Optional[dict] = None
        original_url: Optional[str] = None
        if isinstance(data_object, AbstractAuthorSignaturePage):
            first_author_data: FormattedSignatureData = data_object.get_signature_first_author(request)

            if first_author_data:
                author_data = {
                    'name': first_author_data.title,
                }

                if first_author_data.url.startswith('mailto:'):
                    author_data['email'] = first_author_data.url[7:]
                elif first_author_data.url:
                    author_data['url'] = first_author_data.url

        result = {
            'url': data_object.full_url,
            'date_modified': data_object.last_published_at.isoformat() if data_object.last_published_at else '',
            'date_published': data_object.first_published_at.isoformat() if data_object.first_published_at else '',
            'headline': data_object.title,
            'description': data_object.summary,
            'images': [
                f'{site.root_url}{data_object.image_announce.get_rendition(f).url}'
                for f in ('fill-900x900', 'fill-1200x900', 'fill-1600x900')
            ] if data_object.image_announce else [],
            'organization_name': site.site_name if site.site_name else site.hostname,
            'logo_url': f'{site.root_url}{logo_url}' if logo_url else '',
        }

        if author_data:
            result['author'] = author_data

        if original_url:
            result['original_url'] = original_url

        return result


class PublicationPageManager(PageManager):

    def get_last(self, count: int) -> PageQuerySet:
        return self.live().order_by('-pinned', '-first_published_at')[:count]


class AbstractPublicationPage(AbstractViewsCountablePage, AbstractAuthorSignaturePage, AbstractImageAnnounceSummaryPage,
                              AbstractContentStreamPage):

    class Meta:
        abstract = True

    pinned = models.BooleanField(
        db_index=True,
        default=False,
        verbose_name=_('pinned'),
    )

    cache_prefixes = AbstractAuthorSignaturePage.cache_prefixes + AbstractContentStreamPage.cache_prefixes

    content_panels = Page.content_panels + AbstractImageAnnounceSummaryPage.content_panels + \
        AbstractContentStreamPage.content_panels

    objects = PublicationPageManager()

    opengraph_type = 'article'

    promote_panels = Page.promote_panels + AbstractImageAnnounceSummaryPage.promote_panels + \
        AbstractAuthorSignaturePage.promote_panels

    search_fields = Page.search_fields + AbstractImageAnnounceSummaryPage.search_fields

    settings_panels = Page.settings_panels + [
        FieldPanel('pinned'),
    ]

    structured_data_providers = AbstractContentStreamPage.structured_data_providers + [
        PublicationStructuredDataProvider,
    ]


class AbstractPublicationIndexPage(AbstractBaseIndexPage):

    class Meta:
        abstract = True

    def get_items_class(self) -> Type[Page]:
        raise NotImplementedError

    def get_items_queryset_filters(self, request) -> Optional[Dict]:
        raise NotImplementedError

    def get_per_page_number(self, request) -> int:
        raise NotImplementedError
