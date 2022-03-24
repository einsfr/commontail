from typing import Optional, Dict, Type

from django import forms
from django.db import models
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _lazy

from wagtail.admin.edit_handlers import FieldPanel
from wagtail.core.models import Site, Page
from wagtail.images import get_image_model, get_image_model_string
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.images.models import AbstractRendition
from wagtail.search import index

from .author import AbstractAuthorSignaturePage, FormattedSignatureData
from .opengraph import OpenGraphPageProvider
from .page import AbstractContentStreamPage, AbstractBaseIndexPage
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
            first_author_data: FormattedSignatureData = data_object.get_signature_first_author()

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


class AbstractPublicationPage(AbstractContentStreamPage):

    class Meta:
        abstract = True

    summary = models.CharField(
        blank=True,
        help_text=_lazy('Short description to be used as announce.'),
        max_length=255,
        verbose_name=_lazy('summary'),
    )

    image_announce = models.ForeignKey(
        get_image_model_string(),
        blank=True,
        help_text=_lazy('Image from library to be shown in announce.'),
        null=True,
        on_delete=models.PROTECT,
        related_name='+',
        verbose_name=_lazy('announce image')
    )

    content_panels = Page.content_panels + [
        FieldPanel('summary', widget=forms.Textarea),
        ImageChooserPanel('image_announce'),
    ]

    opengraph_provider = OpenGraphPageProvider(image_attribute='image_announce', description_attribute='summary')
    opengraph_type = 'article'

    search_fields = Page.search_fields + [
        index.SearchField('summary', boost=1.5, partial_match=False),
    ]

    structured_data_providers = AbstractContentStreamPage.structured_data_providers + [
        PublicationStructuredDataProvider,
    ]

    def _get_seo_auto_meta_description(self) -> str:
        return self.summary

    def get_image_announce_or_placeholder(self):
        return self.image_announce or get_image_model().get_no_image_placeholder()


class AbstractPublicationIndexPage(AbstractBaseIndexPage):

    class Meta:
        abstract = True

    def get_items_class(self) -> Type[Page]:
        raise NotImplementedError

    def get_items_queryset_filters(self, request) -> Optional[Dict]:
        raise NotImplementedError

    def get_per_page_number(self, request) -> int:
        raise NotImplementedError
