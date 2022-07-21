from django.db import models
from django.utils.translation import gettext_lazy as _lazy


__all__ = ['AbstractIconAware', 'AbstractSiteHandleModel', ]


class AbstractIconAware:

    def get_icon(self):
        raise NotImplementedError


class AbstractSiteHandleModel(models.Model):

    class Meta:
        abstract = True
        unique_together = (('site', 'handle'), )

    handle = models.SlugField(
        help_text=_lazy('Must be unique per site, will be used as a reference by rendering tag.'),
        max_length=100,
        verbose_name=_lazy('handle'),
    )

    site = models.ForeignKey(
        'wagtailcore.Site',
        on_delete=models.CASCADE,
        related_name='+',
        verbose_name=_lazy('site'),
    )
