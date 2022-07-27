from django.conf import settings
from django.urls import path
from django.views.decorators.cache import cache_page

from wagtail.contrib.sitemaps.views import sitemap
from wagtail.contrib.sitemaps.sitemap_generator import Sitemap as WagtailSitemap

from .views import clear_page_cache_view, ImportIndex, ExportIndex, ImportView, ExportView, RobotsTxtView


__all__ = ['admin_urls', 'robots_urls', ]


admin_urls = [
    path('cache-clear/<int:page_id>/', clear_page_cache_view, name='clear_cache'),
    path('import/', ImportIndex.as_view(), name='import_index'),
    path('import/<str:importer_url_suffix>/', ImportView.as_view(), name='import_view'),
    path('export/', ExportIndex.as_view(), name='export_index'),
    path('export/<str:exporter_url_suffix>/', ExportView.as_view(), name='export_view'),
]

sitemaps = {
    'wagtail': WagtailSitemap,
}

if settings.DEBUG:
    robots_urls = [
        path('robots.txt', RobotsTxtView.as_view()),
        path('sitemap.xml', sitemap, {'sitemaps': sitemaps}),
    ]
else:
    robots_urls = [
        path('robots.txt', cache_page(settings.COMMONTAIL_ROBOTSTXT_CACHE_TIME)(RobotsTxtView.as_view())),
        path('sitemap.xml', cache_page(settings.COMMONTAIL_ROBOTSTXT_CACHE_TIME)(sitemap), {'sitemaps': sitemaps}),
    ]
