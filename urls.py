from django.urls import path

from .views import clear_page_cache_view


__all__ = ['admin_urls', ]


admin_urls = [
    path('commontail-cache-clear/<int:page_id>/', clear_page_cache_view, name='commontail_clear_cache')
]
