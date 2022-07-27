from django.db import models
from django.utils.translation import gettext_lazy as _


__all__ = ['AbstractIconAware', 'AbstractSiteHandleModel', ]


class AbstractIconAware:

    def get_icon(self):
        raise NotImplementedError


class AbstractSiteHandleModel(models.Model):

    class Meta:
        abstract = True
        unique_together = (('site', 'handle'), )

    handle = models.SlugField(
        help_text=_('Must be unique per site, will be used as a reference by rendering tag.'),
        max_length=100,
        verbose_name=_('handle'),
    )

    site = models.ForeignKey(
        'wagtailcore.Site',
        on_delete=models.CASCADE,
        related_name='+',
        verbose_name=_('site'),
    )
