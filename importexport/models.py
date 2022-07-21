from django.db import models
from django.utils.translation import gettext_lazy as _lazy

from wagtail.admin.edit_handlers import FieldPanel, PageChooserPanel


__all__ = ['AbstractPageImporterFormModel', 'AbstractTablePageImporterFormModel', 'AbstractPageCreatorFormModel',
           'AbstractPageUpdaterFormModel', 'AbstractTablePageCreatorFormModel', 'AbstractTablePageUpdaterFormModel']


class AbstractPageImporterFormModel(models.Model):

    class Meta:
        abstract = True

    file = models.FileField(
        verbose_name=_lazy('file')
    )

    simulation = models.BooleanField(
        default=True,
        verbose_name=_lazy('simulation')
    )

    edit_handler_list = [FieldPanel('file'), FieldPanel('simulation'), ]


class AbstractTablePageImporterFormModel(AbstractPageImporterFormModel):

    class Meta:
        abstract = True

    first_data_row = models.PositiveIntegerField(
        default=1,
        verbose_name=_lazy('first row with data'),
    )

    id_column = models.PositiveIntegerField(
        verbose_name=_lazy('id_column'),
    )

    last_data_row = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_lazy('last row with data'),
    )

    edit_handler_list = AbstractPageImporterFormModel.edit_handler_list + [
        FieldPanel('first_data_row'), FieldPanel('last_data_row'), FieldPanel('id_column'),
    ]


class AbstractPageCreatorFormModel(AbstractPageImporterFormModel):

    class Meta:
        abstract = True

    parent_page = models.ForeignKey(
        'wagtailcore.Page',
        on_delete=models.CASCADE,
        verbose_name=_lazy('parent page'),
    )

    edit_handler_list = [PageChooserPanel('parent_page'), ]


class AbstractTablePageCreatorFormModel(AbstractPageCreatorFormModel, AbstractTablePageImporterFormModel):

    class Meta:
        abstract = True


class AbstractPageUpdaterFormModel(AbstractPageImporterFormModel):

    class Meta:
        abstract = True


class AbstractTablePageUpdaterFormModel(AbstractPageUpdaterFormModel, AbstractTablePageImporterFormModel):

    class Meta:
        abstract = True
