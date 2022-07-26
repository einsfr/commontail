from datetime import datetime
from typing import Optional, Iterable, Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _lazy

from modelcluster.models import ClusterableModel
from modelcluster.fields import ParentalKey

from wagtail.admin.edit_handlers import FieldPanel, InlinePanel
from wagtail.core.models import Orderable
from wagtail.images import get_image_model_string
from wagtail.images.edit_handlers import ImageChooserPanel

from .cache import AbstractCacheAware, CacheMeta
from .links import AbstractLinkFields
from .utils import AbstractSiteHandleModel


__all__ = ['Banner', 'BannerSet', 'BannerSetItem', ]


class Banner(AbstractLinkFields):

    class Meta:
        verbose_name = _lazy('banner')
        verbose_name_plural = _lazy('banners')

    active_since = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_lazy('active since'),
    )

    active_to = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_lazy('active to'),
    )

    enabled = models.BooleanField(
        default=True,
        verbose_name=_lazy('enabled'),
    )

    is_active = models.BooleanField(
        editable=False,
    )

    title = models.CharField(
        help_text=_lazy('Title to use in administrative area.'),
        max_length=255,
        verbose_name=_lazy('title'),
    )

    image = models.ForeignKey(
        get_image_model_string(),
        on_delete=models.PROTECT,
        related_name='+',
        verbose_name=_lazy('image'),
    )

    panels = [
        FieldPanel('title'),
        FieldPanel('enabled'),
        FieldPanel('active_since'),
        FieldPanel('active_to'),
        ImageChooserPanel('image'),
    ] + AbstractLinkFields.panels

    def __str__(self):
        return self.title

    def clean(self):
        if self.active_since and self.active_to:
            if self.active_since > self.active_to:
                raise ValidationError('Activity start date is less than activity end date.')

        super().clean()

    def save(self, force_insert=False, force_update=False, using=None,  # TODO: Banner activity management command
             update_fields=None):
        if self.enabled:
            now: datetime = timezone.now()
            self.is_active = ((self.active_to if self.active_to else now) >= now >= (
                self.active_since if self.active_since else now))
        else:
            self.is_active = False

        super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)


class BannerSet(AbstractCacheAware, AbstractSiteHandleModel, ClusterableModel):

    class Meta(AbstractSiteHandleModel.Meta):
        verbose_name = _lazy('banners set')
        verbose_name_plural = _lazy('banners sets')

    delay = models.PositiveSmallIntegerField(
        default=10,
        validators=[MinValueValidator(5), ],
        verbose_name=_lazy('duration'),
    )

    title = models.CharField(
        help_text=_lazy('Title to use in administrative area.'),
        max_length=255,
        verbose_name=_lazy('title'),
    )

    cache_template_prefix = 'banner_template'

    cache_prefixes = AbstractCacheAware.cache_prefixes + {
        cache_template_prefix: CacheMeta(
            ('template_fragments', 'default'),
            settings.COMMONTAIL_BANNER_CACHE_LIFETIME
        )
    }

    panels = [
        FieldPanel('title'),
        FieldPanel('handle'),
        FieldPanel('delay'),
        FieldPanel('site'),
        InlinePanel('items', label=_lazy('Items')),
    ]

    def __str__(self):
        return self.title

    def get_cache_vary_on(self) -> Iterable[Any]:
        return self.site_id, self.handle

    def get_template(self, context: dict = None) -> list[str]:
        templates_list: list[str] = []

        template_name: Optional[str] = context.get('template_name', None)
        if template_name:
            templates_list.append(f'commontail/banner/banner.{template_name}.html')

        templates_list.extend([
            f'commontail/banner/banner.{self.handle}.html',
            f'commontail/banner/banner.html',
        ])

        return templates_list


class BannerSetItem(Orderable):

    banner = models.ForeignKey(
        Banner,
        on_delete=models.PROTECT,
        related_name='banner_set_item',
        verbose_name=_lazy('banner'),
    )

    banner_set = ParentalKey(
        BannerSet,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_lazy('banners set'),
    )
