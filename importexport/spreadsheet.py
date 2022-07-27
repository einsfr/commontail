from typing import Callable, Iterable, Optional, Type

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils.translation import gettext_lazy as _

from wagtail.admin.edit_handlers import ObjectList, FieldPanel

from .abstract import AbstractPageImporter
from .models import AbstractPageImporterFormModel, AbstractTablePageCreatorFormModel, AbstractTablePageUpdaterFormModel


__all__ = ['AbstractSpreadsheetImporter', 'AbstractSpreadsheetUpdater', 'AbstractSpreadsheetCreator']


class AbstractSpreadsheetImporter(AbstractPageImporter):

    def call_updater(self, update_callable, page, row, col_number, attr, simulation, **kwargs):
        if update_callable in (self.update_int_range_value, self.update_float_range_value):
            return update_callable(page, getattr(page, self.page_id_attr),
                                   (row[col_number - 1].value, row[col_number].value), attr, simulation,
                                   **kwargs)
        else:
            return update_callable(page, getattr(page, self.page_id_attr),
                                   row[col_number - 1].value, attr, simulation, **kwargs)

    @classmethod
    def get_base_form_model(cls) -> Type[AbstractPageImporterFormModel]:
        raise NotImplementedError

    @classmethod
    def get_columns(cls) -> Iterable[tuple[str, str, Callable, Optional[dict]]]:
        return [
            ('title', _('title'), cls.update_str_value, None),
            ('slug', _('slug'), cls.update_str_value, None),
        ]

    @classmethod
    def get_form_model(cls) -> Type[AbstractPageImporterFormModel]:
        if cls.form_model is not None:
            return cls.form_model

        base_form_model: Type[AbstractPageImporterFormModel] = cls.get_base_form_model()
        attrs: dict = {'__module__': __name__}
        edit_handler_list: list = getattr(base_form_model, 'edit_handler_list', [])

        col_name: str
        verbose_name: str
        for col_name, verbose_name, *other in cls.get_columns():
            attr_name: str = f'{col_name}_column'
            attrs[attr_name] = models.PositiveIntegerField(blank=True, null=True, verbose_name=verbose_name)
            edit_handler_list.append(FieldPanel(attr_name))

        attrs['edit_handler'] = ObjectList(edit_handler_list)

        cls.form_model = type('ImporterModel', (base_form_model, ), attrs)

        return cls.form_model

    def get_page(self, id_value):
        raise NotImplementedError

    def get_page_model(self):
        raise NotImplementedError

    def get_worksheet(self):
        try:
            import openpyxl
        except ImportError:
            raise RuntimeError(_('openpyxl needed to work with spreadsheet files.'))
        worksheet = openpyxl.load_workbook(
            self.form.cleaned_data['file'], read_only=True, data_only=True).worksheets[0]

        return worksheet

    def page_exists(self, id_value):
        raise NotImplementedError

    def post_form_processing_hook(self):
        return

    def post_save_hook(self, page, parent_page, id_value):
        return

    def pre_save_hook(self, page, parent_page, id_value):
        return

    def process_form(self):
        processed_pages: int = 0
        loaded_pages: int = 0
        errors: list[str] = []
        worksheet = self.get_worksheet()
        col_id: int = self.form.cleaned_data['id_column']
        simulation: bool = self.form.cleaned_data['simulation']
        if simulation:
            warnings = [_('THIS IS A SIMULATION - NO CHANGES WERE MADE.')]
        else:
            warnings = []
        for row in worksheet.iter_rows(min_row=self.form.cleaned_data['first_data_row'],
                                       max_row=self.form.cleaned_data['last_data_row']):
            processed_pages, loaded_pages = self.process_row(row, col_id, warnings, errors, processed_pages,
                                                             loaded_pages, simulation)
        self.post_form_processing_hook()

        return processed_pages, loaded_pages, warnings, errors

    def process_row(self, row, col_id, warnings, errors, processed_pages, loaded_pages, simulation):
        raise NotImplementedError

    def save_page(self, page, id_value, warnings, errors, simulation):
        loaded_pages: int = 0
        try:
            if simulation:
                page.full_clean()
            else:
                page.save()
                revision = page.save_revision(user=self.request.user)
                if page.live:
                    revision.publish()
        except Exception as e:
            errors.append(
                _(
                    'Page <id:%(item_id)s> - errors while updating: "%(errors)s".'
                ) % {'item_id': id_value, 'errors': repr(e)}
            )
        else:
            loaded_pages = 1

        return loaded_pages


class AbstractSpreadsheetCreator(AbstractSpreadsheetImporter):

    @classmethod
    def get_base_form_model(cls):
        return AbstractTablePageCreatorFormModel

    def get_page(self, id_value):
        raise NotImplementedError

    def get_page_model(self):
        raise NotImplementedError

    def page_exists(self, id_value):
        raise NotImplementedError

    def process_row(self, row, col_id, warnings, errors, processed_pages, loaded_pages, simulation):
        id_value = row[col_id - 1].value
        if not id_value:
            return processed_pages, loaded_pages
        id_value = self.multispace_re.sub(' ', str(id_value)).strip()

        processed_pages += 1

        if self.page_exists(id_value):
            warnings.append(_('Page <id:%(item_id)s> already exists - skipping...') % {'item_id': id_value})

            return processed_pages, loaded_pages

        parent_page = self.form.cleaned_data['parent_page'].specific
        page_class = self.get_page_model()
        if page_class not in parent_page.creatable_subpage_models() or not page_class.can_create_at(parent_page):
            errors.append(
                _(
                    'Page <id:%(item_id)s> with class "%(page_class)s" could not be created with parent '
                    '"%(parent_class)s".'
                ) % {'item_id': id_value, 'page_class': page_class, 'parent_class': parent_page.__class__}
            )

        page = page_class()

        for attr, other, update_callable, kwargs in self.get_columns():
            col_number = self.form.cleaned_data.get(f'{attr}_column', None)
            if not col_number:
                continue
            kwargs = kwargs if kwargs is not None else dict()
            u, w, e = self.call_updater(update_callable, page, row, col_number, attr, simulation, **kwargs)
            warnings.extend(w)
            errors.extend(e)

        last_child = parent_page.get_last_child()
        if last_child is None:
            page.path = f'{parent_page.path}{page.alphabet[0] * (page.steplen - 1)}{page.alphabet[1]}'
        else:
            page.path = last_child._inc_path()

        page.depth = parent_page.depth + 1
        page.numchild = 0
        page.live = True
        page.set_url_path(parent_page)
        page.owner = self.request.user
        self.pre_save_hook(page, parent_page, id_value)
        loaded_pages += self.save_page(page, id_value, warnings, errors, simulation)
        self.post_save_hook(page, parent_page, id_value)
        parent_page.numchild += loaded_pages
        parent_page.save()

        return processed_pages, loaded_pages


class AbstractSpreadsheetUpdater(AbstractSpreadsheetImporter):

    @classmethod
    def get_base_form_model(cls) -> Type[AbstractPageImporterFormModel]:
        return AbstractTablePageUpdaterFormModel

    def get_page(self, id_value):
        raise NotImplementedError

    def get_page_model(self):
        raise NotImplementedError

    def page_exists(self, id_value):
        raise NotImplementedError

    def process_row(self, row, col_id, warnings, errors, processed_pages, loaded_pages, simulation):
        id_value = row[col_id - 1].value
        if not id_value:
            return processed_pages, loaded_pages
        id_value = self.multispace_re.sub(' ', str(id_value)).strip()

        try:
            page = self.get_page(id_value)
        except ObjectDoesNotExist:
            warnings.append(_('Page <id:%(item_id)s> not found.') % {'item_id': id_value})

            return processed_pages, loaded_pages

        updated = False
        processed_pages += 1

        for attr, other, update_callable, kwargs in self.get_columns():
            col_number = self.form.cleaned_data.get(f'{attr}_column', None)
            if not col_number:
                continue
            kwargs = kwargs if kwargs is not None else dict()
            u, w, e = self.call_updater(update_callable, page, row, col_number, attr, simulation, **kwargs)
            updated = updated or u
            warnings.extend(w)
            errors.extend(e)

        if not updated:
            return processed_pages, loaded_pages

        loaded_pages += self.save_page(page, id_value, warnings, errors, simulation)

        return processed_pages, loaded_pages
