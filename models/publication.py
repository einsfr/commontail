from typing import Optional, Type, Dict, Union, Iterable

from django import forms
from django.db import models
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from wagtail.admin.panels import FieldPanel
from wagtail.embeds.embeds import get_embed, Embed
from wagtail.embeds.exceptions import EmbedException
from wagtail.models import Site, Page, PageManager, PageQuerySet
from wagtail.images.models import AbstractRendition

from .author import AbstractAuthorSignaturePage, FormattedSignatureData, Author
from .counter import AbstractViewsCountablePage
from .page import AbstractContentStreamPage, AbstractBaseIndexPage, AbstractImageAnnounceSummaryPage
from .settings import get_logo_rendition
from .structureddata import AbstractStructuredDataProvider


__all__ = ['AbstractPublicationPage', 'AbstractPublicationMediaPage', 'AbstractPublicationIndexPage',
           'PublicationStructuredDataProvider', ]


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
                    'email': first_author_data.email,
                    'name': first_author_data.title,
                    'url': first_author_data.url,
                }

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

    objects = PublicationPageManager()

    opengraph_type = 'article'

    settings_panels = [
        FieldPanel('pinned'),
    ]

    structured_data_providers = AbstractContentStreamPage.structured_data_providers + [
        PublicationStructuredDataProvider,
    ]


class AbstractPublicationMediaPage(AbstractPublicationPage):

    class Meta:
        abstract = True

    media_url = models.URLField(
        verbose_name=_('media URL'),
    )

    media_embed_max_width: int = 640

    media_embed_max_height: int = 360

    content_panels = [
        FieldPanel('media_url'),
    ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        embedded_media: Optional[Embed]
        try:
            embedded_media = get_embed(self.media_url, max_width=self.media_embed_max_width,
                                       max_height=self.media_embed_max_height)
        except EmbedException:
            embedded_media = None

        context.update({
            'media': embedded_media,
        })

        return context


class AbstractPublicationIndexPage(AbstractBaseIndexPage):

    class Meta:
        abstract = True

    def get_items_class(self) -> Type[Page]:
        raise NotImplementedError

    def get_items_queryset_filters(self, filters_form: forms.BaseForm, request: HttpRequest) \
            -> Optional[Union[Dict, models.Q, Iterable[models.Q]]]:
        author: Author = filters_form.cleaned_data['author']
        if author:
            return author.get_pages_q(Site.find_for_request(request))

    def get_filters_form_fields(self, request: HttpRequest) -> Optional[Dict[str, forms.Field]]:
        return {
            'author': forms.ModelChoiceField(
                label=_('Author'),
                queryset=Author.objects.exists_in_descendants(self).order_by('first_name'),
                required=False,
                widget=forms.Select(attrs={'class': 'uk-select'})
            ),
        }

    def get_per_page_number(self, request) -> int:
        raise NotImplementedError
