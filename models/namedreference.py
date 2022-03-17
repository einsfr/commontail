from django.db import models
from django.utils.translation import gettext_lazy as _lazy

from wagtail.admin.edit_handlers import FieldPanel
from wagtail.core.models import Site

from .links import AbstractLinkFields


__all__ = ['NamedReference', ]


class NamedReference(AbstractLinkFields):

    class Meta:
        verbose_name = _lazy('named reference')
        verbose_name_plural = _lazy('named references')
        unique_together = (('site', 'handle'), )

    handle = models.CharField(
        max_length=255,
        verbose_name=_lazy('handle'),
    )

    site = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
        verbose_name=_lazy('site'),
        related_name='+',
    )

    panels = [
        FieldPanel('site'),
        FieldPanel('handle'),
    ] + AbstractLinkFields.panels

    def __str__(self):
        return f'{self.site}: {self.handle}'
