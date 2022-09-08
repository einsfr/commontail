from typing import Optional

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField

from .utils import AbstractSiteHandleModel


__all__ = ['Hint', ]


class Hint(AbstractSiteHandleModel):

    class Meta(AbstractSiteHandleModel.Meta):
        verbose_name = _('hint')
        verbose_name_plural = _('hints')

    summary = models.CharField(
        blank=True,
        max_length=100,
        verbose_name=_('summary'),
    )

    text = RichTextField(
        blank=True,
        features=settings.COMMONTAIL_RTF_LIMITED_FEATURES,
        max_length=1000,
        verbose_name=_('text'),
    )

    title = models.CharField(
        help_text=_('Title to use in administrative area.'),
        max_length=255,
        verbose_name=_('title'),
    )

    panels = [
        FieldPanel('title'),
        FieldPanel('handle'),
        FieldPanel('summary'),
        FieldPanel('text'),
        FieldPanel('site'),
    ]

    def __str__(self):
        return self.title

    def get_template(self, context: dict = None) -> list[str]:
        templates_list: list[str] = []

        template_name: Optional[str] = context.get('template_name', None)
        if template_name:
            templates_list.append(f'commontail/hint/hint.{template_name}.html')

        templates_list.extend([
            f'commontail/hint/hint.{self.handle}.html',
            f'commontail/hint/hint.html',
        ])

        return templates_list
