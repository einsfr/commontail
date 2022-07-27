from django.db import models, IntegrityError
from django.utils.translation import gettext_lazy as _lazy
from django.utils.functional import cached_property

from wagtail.core.models import Page


__all__ = ['PageViewsCounter', 'AbstractViewsCountablePage', ]


class PageViewsCounter(models.Model):

    class Meta:
        verbose_name = 'счётчик посещений'
        verbose_name_plural = 'счётчики посещений'

    page = models.OneToOneField(
        'wagtailcore.Page',
        related_name='views_counter',
        on_delete=models.CASCADE,
        primary_key=True,
        verbose_name=_lazy('page'),
    )

    views_count = models.PositiveBigIntegerField(
        db_index=True,
        verbose_name=_lazy('views count'),
    )


class AbstractViewsCountablePage(Page):

    class Meta:
        abstract = True

    @cached_property
    def views_count(self) -> int:
        return self.views_counter.views_count

    def increment_views_count(self, request):
        PageViewsCounter.objects.filter(page_id=self.pk).update(views_count=models.F('views_count') + 1)

    def serve(self, request, *args, **kwargs):
        if (request.headers.get('x-requested-with') != 'XMLHttpRequest') and not getattr(request, 'is_preview', False):
            # robots included - user-agent checking in each request needed - may be slow, or may be not
            self.increment_views_count(request)

        return super().serve(request, *args, **kwargs)
