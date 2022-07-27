import os.path

from typing import Optional

from django.db import models
from django.conf import settings
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from wagtail.contrib.settings.models import BaseSetting, register_setting
from wagtail.core.models import Site
from wagtail.images import get_image_model_string
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.images.models import AbstractRendition, AbstractImage


__all__ = ['CommonSettings', 'get_logo', 'get_logo_rendition', 'get_logo_original_path', 'get_logo_rendition_path',
           'get_docs_background', 'get_docs_background_path', 'PerPageSettingsMixin']


@register_setting
class CommonSettings(BaseSetting):

    class Meta:
        verbose_name = _('common')
        verbose_name_plural = _('common')

    logo = models.ForeignKey(
        get_image_model_string(),
        on_delete=models.PROTECT,
        verbose_name=_('main logo'),
        related_name='+',
        null=True,
        blank=True,
    )

    logo_square = models.ForeignKey(
        get_image_model_string(),
        on_delete=models.PROTECT,
        verbose_name=_('square logo'),
        related_name='+',
        null=True,
        blank=True,
    )

    docs_background = models.ForeignKey(
        get_image_model_string(),
        on_delete=models.PROTECT,
        verbose_name=_('printable docs background'),
        related_name='+',
        null=True,
        blank=True,
    )

    panels = [
        ImageChooserPanel('logo'),
        ImageChooserPanel('logo_square'),
        ImageChooserPanel('docs_background'),
    ]


def get_logo(site: Optional[Site] = None, request: Optional[HttpRequest] = None,
             square: bool = False) -> Optional[AbstractImage]:
    """
    Returns logo, defined in CommonSettings for site

    :param site: Site
    :param request: HttpRequest
    :param square: if True - returns square version
    :return: AbstractImage object or None if logo is not defined
    """
    if not site:
        if not request:
            raise ValueError('get_logo function requires not-None site or request argument.')
        else:
            site: Site = Site.find_for_request(request)

    if square:
        return CommonSettings.for_site(site).logo_square
    else:
        return CommonSettings.for_site(site).logo


def get_logo_rendition(site: Optional[Site] = None, request: Optional[HttpRequest] = None, square: bool = False,
                       filter_spec: str = None) -> Optional[AbstractRendition]:
    """
    Returns rendition for logo, defined in CommonSettings for site

    :param site: Site
    :param request: HttpRequest
    :param square: if True - returns square version
    :param filter_spec: a filter specification for rendition ('original' if None passed)
    :return: AbstractRendition object or None if logo is not defined
    """
    try:
        return get_logo(site, request, square).get_rendition(filter_spec if filter_spec else 'original')
    except AttributeError:
        return None


def get_logo_original_path(site: Optional[Site] = None, request: Optional[HttpRequest] = None,
                           square: bool = False) -> Optional[str]:
    """
    Returns path to original logo file, defined in CommonSettings for site

    :param site: Site
    :param request: HttpRequest
    :param square: if True - returns path to square version
    :return: path to original file or None if logo is not defined
    """
    try:
        return os.path.join(settings.MEDIA_ROOT, str(get_logo(site, request, square).file))
    except AttributeError:
        return None


def get_logo_rendition_path(site: Optional[Site] = None, request: Optional[HttpRequest] = None, square: bool = False,
                            filter_spec: str = None) -> Optional[str]:
    """
    Returns path to rendition file of logo, defined in CommonSettings for site

    :param site: Site
    :param request: HttpRequest
    :param square: if True - returns path to square version
    :param filter_spec: a filter specification for rendition ('original' if None passed)
    :return: path to rendition file or None if logo is not defined
    """
    try:
        return os.path.join(settings.MEDIA_ROOT, str(get_logo_rendition(site, request, square, filter_spec).file))
    except AttributeError:
        return None


def get_docs_background(site: Optional[Site] = None, request: Optional[HttpRequest] = None) -> Optional[AbstractImage]:
    """
    Returns printable documents background, defined in CommonSettings for site

    :param site: Site
    :param request: HttpRequest
    :return: AbstractImage object or None if documents background is not defined
    """
    if not site:
        if not request:
            raise ValueError('get_docs_background function requires not-None site or request argument.')
        else:
            site: Site = Site.find_for_request(request)

    return CommonSettings.for_site(site).docs_background


def get_docs_background_path(site: Optional[Site] = None, request: Optional[HttpRequest] = None) -> Optional[str]:
    """
    Returns path to documents background file, defined in CommonSettings for site

    :param site: Site
    :param request: HttpRequest
    :return: path to documents background or None if documents background is not defined
    """
    try:
        return os.path.join(settings.MEDIA_ROOT, str(get_docs_background(site, request).file))
    except AttributeError:
        return None


class PerPageSettingsMixin(models.Model):

    class Meta:
        abstract = True

    items_per_page = models.PositiveSmallIntegerField(
        verbose_name=_('items per page'),
        default=10,
        help_text=_('Items quantity per index page.'),
    )
