from django.http.response import HttpResponseForbidden

from wagtail.core.models import Page


__all__ = ['HierarchyOnlyPage', ]


class HierarchyOnlyPage(Page):

    class Meta:
        abstract = True

    is_not_accessible = True

    def get_sitemap_urls(self, request=None):
        return []

    def serve(self, request, *args, **kwargs):
        return HttpResponseForbidden()
