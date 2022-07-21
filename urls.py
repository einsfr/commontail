from django.urls import path

from .views import clear_page_cache_view, ImportIndex, ExportIndex, ImportView, ExportView


__all__ = ['admin_urls', ]


admin_urls = [
    path('cache-clear/<int:page_id>/', clear_page_cache_view, name='clear_cache'),
    path('import/', ImportIndex.as_view(), name='import_index'),
    path('import/<str:importer_url_suffix>/', ImportView.as_view(), name='import_view'),
    path('export/', ExportIndex.as_view(), name='export_index'),
    path('export/<str:exporter_url_suffix>/', ExportView.as_view(), name='export_view'),
]
