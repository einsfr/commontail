from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import Http404
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.generic.base import TemplateView
from django.views.generic.edit import ProcessFormView

from wagtail.admin import messages

from ..importexport import get_importers, get_importer_by_url_suffix, get_exporters, get_exporter_by_url_suffix


__all__ = ['ImportIndex', 'ExportIndex', 'ImportView', 'ExportView', ]


class ImportIndex(PermissionRequiredMixin, TemplateView):

    template_name = 'commontail/admin/import_index.html'
    permission_required = 'commontail_can_import_data'

    def get_context_data(self, **kwargs):
        context = super(ImportIndex, self).get_context_data(**kwargs)
        context['importers'] = [
            {
                'title': i.title,
                'url': reverse('commontail_admin:import_view', kwargs={'importer_url_suffix': i.url_suffix})
            }
            for i in get_importers()
        ]

        return context


class ExportIndex(PermissionRequiredMixin, TemplateView):

    template_name = 'commontail/admin/export_index.html'
    permission_required = 'commontail_can_export_data'

    def get_context_data(self, **kwargs):
        context = super(ExportIndex, self).get_context_data(**kwargs)
        context['exporters'] = [
            {
                'title': e.title,
                'url': reverse('commontail_admin:export_view', kwargs={'exporter_url_suffix': e.url_suffix})
            }
            for e in get_exporters()
        ]

        return context


class AbstractImportExportView(PermissionRequiredMixin, ProcessFormView, TemplateView):

    http_method_names = ['get', 'post']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.form_model = None
        self.edit_handler_class = None
        self.form_class = None

    def get_form(self):
        if self.request.method == 'POST':
            form = self.form_class(self.request.POST, self.request.FILES)
        else:
            form = self.form_class()

        return form

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data())


class ImportView(AbstractImportExportView):

    template_name = 'commontail/admin/import_form.html'
    permission_required = 'commontail_can_import_data'
    # User may not have per page permission. If he has import permission - he can import pages

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.importer = None

    def dispatch(self, request, *args, **kwargs):
        self.importer = get_importer_by_url_suffix(self.kwargs['importer_url_suffix'])
        if not self.importer:
            raise Http404(
                _('Importer for %(url_suffix)s not found.') % {'url_suffix': self.kwargs['importer_url_suffix']}
            )

        self.form_model = self.importer.get_form_model()
        self.edit_handler_class = self.form_model.edit_handler.bind_to(model=self.form_model)
        self.form_class = self.edit_handler_class.get_form_class()

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = {
            'title': self.importer.title,
            'edit_handler': self.edit_handler_class.bind_to(instance=self.form_model(), form=self.get_form(),
                                                            request=self.request)
        }
        context.update(kwargs)

        return super().get_context_data(**context)

    def form_valid(self, form):
        try:
            processed_pages, loaded_pages, warnings, errors = self.importer(self.request, form).process_form()
        except Exception as e:
            messages.error(self.request, f"{_('Error while importing data: ')}{str(e)}.")
            processed_pages = 0
            loaded_pages = 0
            warnings = []
            errors = []

        context = self.get_context_data()
        context.update({
            'complete': True,
            'processed_pages': processed_pages,
            'loaded_pages': loaded_pages,
            'warnings': warnings,
            'errors': errors,
        })

        return self.render_to_response(context)


class ExportView(AbstractImportExportView):
    template_name = 'commontail/admin/export_form.html'
    permission_required = 'commontail_can_export_data'
    # User may not have per page permission. If he has export permission - he can export pages

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.exporter = None

    def dispatch(self, request, *args, **kwargs):
        self.exporter = get_exporter_by_url_suffix(self.kwargs['exporter_url_suffix'])
        if not self.exporter:
            raise Http404(
                _('Exporter for %(url_suffix)s not found.') % {'url_suffix': self.kwargs['exporter_url_suffix']}
            )

        self.form_model = self.exporter.get_form_model()
        self.edit_handler_class = self.form_model.edit_handler.bind_to(model=self.form_model)
        self.form_class = self.edit_handler_class.get_form_class()

        return super(ExportView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = {
            'title': self.exporter.title,
            'edit_handler': self.edit_handler_class.bind_to(instance=self.form_model(), form=self.get_form())
        }
        context.update(kwargs)

        return super(ExportView, self).get_context_data(**context)

    def form_valid(self, form):
        pass
