from typing import Optional

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext as _, gettext_lazy as _lazy

from modelcluster.models import ClusterableModel, ParentalKey

from wagtail.admin.edit_handlers import FieldPanel, PageChooserPanel, InlinePanel
from wagtail.core.models import Orderable
from wagtail.documents.edit_handlers import DocumentChooserPanel
from wagtail.images import get_image_model_string
from wagtail.images.edit_handlers import ImageChooserPanel

from .icon import AbstractIconAware


__all__ = ['AbstractPageLink', 'BaseLinkFields', 'DEFAULT_PAGE_LINKS_CATEGORIES_GROUP_HANDLE', 'LinkedDocument', 'LinkedImage', 'LinkFields', 'PageLinkCategory', 'PageLinkCategoryGroup', 'PageLinkCategoryToPageLinkCategoryGroup', ]


DEFAULT_PAGE_LINKS_CATEGORIES_GROUP_HANDLE: str = 'all'


class BaseLinkFields(models.Model):

    class Meta:
        abstract = True

    email = models.EmailField(
        verbose_name=_lazy('email address'),
        blank=True,
        help_text=_lazy('email address to be used as a link.')
    )

    link_document = models.ForeignKey(
        'wagtaildocs.Document',
        verbose_name=_lazy('link to a document'),
        null=True,
        blank=True,
        related_name='+',
        on_delete=models.CASCADE,
        help_text=_lazy('Link to a document on this site.')
    )

    link_external = models.URLField(
        verbose_name=_lazy('external link'),
        blank=True,
        help_text='Link to external URL. Must be used with "Link\'s test" field.'
    )

    link_page = models.ForeignKey(
        'wagtailcore.Page',
        verbose_name=_lazy('link to a page'),
        null=True,
        blank=True,
        related_name='+',
        on_delete=models.CASCADE,
        help_text=_lazy('Link to a page on this site. "Query string" field may be used.')
    )

    query_string = models.CharField(
        max_length=255,
        verbose_name=_lazy('query string for a page link'),
        blank=True,
        help_text=_lazy('Query string parameters without opening ?.')
    )

    panels = [
        FieldPanel('link_external'),
        PageChooserPanel('link_page'),
        FieldPanel('query_string'),
        DocumentChooserPanel('link_document'),
        FieldPanel('email'),
    ]

    @property
    def url(self) -> str:
        if self.link_page:
            return f'{self.link_page.url}?{self.query_string}' if self.query_string else self.link_page.url
        elif self.link_document:
            return self.link_document.url
        elif self.email:
            return f'mailto:{self.email}'
        else:
            return self.link_external

    def clean(self):
        links_count: int = bool(self.link_page) + bool(self.link_document) + bool(self.link_external) + bool(self.email)
        msg: Optional[str] = None
        if links_count == 0:
            msg = _('One link must be set.')
        if links_count > 1:
            msg = _('Only one link may be set - choose it and remove others.')
        if msg:
            raise ValidationError({
                'link_external': msg,
                'link_page': msg,
                'link_document': msg,
                'email': msg,
            })
        if self.query_string and not self.link_page:
            msg = _('Query string may be used with page links only.')
            raise ValidationError({
                'query_string': msg,
            })
        super().clean()


class LinkFields(BaseLinkFields):  # https://github.com/wagtail/wagtaildemo/blob/master/demo/models.py

    class Meta:
        abstract = True

    link_text = models.CharField(
        verbose_name=_lazy('link\'s text'),
        blank=True,
        max_length=255,
        help_text=_lazy('Link\'s text. Required for external links only. '
                        'May be used as substitute text with page and document links.')
    )

    panels = BaseLinkFields.panels + [
        FieldPanel('link_text'),
    ]

    @property
    def icon(self):
        if self.link_page:
            specific_page = self.link_page.specific
            if isinstance(specific_page, AbstractIconAware):
                return specific_page.get_icon()
        elif self.link_document:
            # TODO: different icons may appear according to the document type - default only by now
            return settings.COMMONTAIL_LINK_ICON_DOCUMENT_DEFAULT
        else:
            return settings.COMMONTAIL_LINK_ICON_EXTERNAL

    @property
    def text(self):
        if self.link_text:
            return self.link_text
        elif self.link_page:
            return self.link_page.title
        elif self.link_document:
            return self.link_document.title

    def clean(self):
        if self.link_external and not self.link_text:
            msg = _('This field is required with external links.')
            raise ValidationError({
                'link_text': msg,
            })
        super().clean()


class LinkedDocument(models.Model):

    class Meta:
        abstract = True
        verbose_name = _lazy('linked document')
        verbose_name_plural = _lazy('linked documents')

    document = models.ForeignKey(
        'wagtaildocs.Document',
        verbose_name=_('document'),
        related_name='+',
        on_delete=models.CASCADE,
        help_text=_lazy('Document on this site.')
    )

    inherit = models.BooleanField(
        verbose_name=_lazy('allow inheritance'),
        default=True,
    )

    panels = [
        DocumentChooserPanel('document'),
        FieldPanel('inherit'),
    ]

    @property
    def title(self):
        return self.document.title

    @property
    def created_at(self):
        return self.document.created_at

    @property
    def url(self):
        return self.document.url

    @property
    def file_extension(self):
        return self.document.file_extension

    @property
    def file_size(self):
        return self.get_file_size()

    def get_file_size(self):
        return self.document.get_file_size()


class LinkedImage(Orderable):

    class Meta(Orderable.Meta):
        abstract = True
        verbose_name = _lazy('linked image')
        verbose_name_plural = _lazy('linked_images')

    image = models.ForeignKey(
        get_image_model_string(),
        verbose_name=_lazy('image'),
        related_name='+',
        on_delete=models.CASCADE,
        help_text=_lazy('Image on this site.')
    )

    inherit = models.BooleanField(
        verbose_name=_lazy('allow inheritance'),
        default=True,
    )

    panels = [
        ImageChooserPanel('image'),
        FieldPanel('inherit'),
    ]


class PageLinkCategory(models.Model):

    class Meta:
        verbose_name = _lazy('category of a page-to-page link')
        verbose_name_plural = _lazy('categories of page-to-page links')

    title = models.CharField(
        verbose_name=_lazy('title'),
        max_length=255,
        unique=True,
    )

    panels = [
        FieldPanel('title'),
    ]

    def __str__(self):
        return self.title

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        is_new: bool = not self.pk
        super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)

        if is_new:
            group: PageLinkCategoryGroup = PageLinkCategoryGroup.objects.get(
                handle=DEFAULT_PAGE_LINKS_CATEGORIES_GROUP_HANDLE)
            max_order: int = group.category_relations.aggregate(models.Max('sort_order'))['sort_order__max']

            PageLinkCategoryToPageLinkCategoryGroup.objects.create(
                category=self,
                group=group,
                sort_order=max_order + 1,
            )


class PageLinkCategoryGroup(ClusterableModel):

    class Meta:
        verbose_name = _lazy('page-to-page link categories group')
        verbose_name_plural = _lazy('page-to-page link categories groups')

    title = models.CharField(
        verbose_name=_lazy('title'),
        max_length=255,
    )

    handle = models.CharField(
        verbose_name=_lazy('handle'),
        max_length=255,
        unique=True,
    )

    panels = [
        FieldPanel('title'),
        FieldPanel('handle'),
        InlinePanel('category_relations', label=_lazy('Categories')),
    ]

    def __str__(self):
        return self.title


class PageLinkCategoryToPageLinkCategoryGroup(Orderable):

    class Meta(Orderable.Meta):
        unique_together = (('category', 'group'), )

    category = models.ForeignKey(
        PageLinkCategory,
        on_delete=models.CASCADE,
        related_name='+',
        verbose_name=_lazy('category'),
    )

    group = ParentalKey(
        PageLinkCategoryGroup,
        on_delete=models.CASCADE,
        related_name='category_relations',
        verbose_name=_lazy('group'),
    )

    panels = [
        FieldPanel('category'),
    ]


class AbstractPageLink(Orderable):

    class Meta(Orderable.Meta):
        abstract = True
        verbose_name = _lazy('page-to-page link')
        verbose_name_plural = _lazy('page-to-page links')

    category = models.ForeignKey(
        PageLinkCategory,
        on_delete=models.PROTECT,
        related_name='+',
        verbose_name=_lazy('category'),
    )

    inherit = models.BooleanField(
        verbose_name=_lazy('allow inheritance'),
        default=True,
    )

    target = models.ForeignKey(
        'wagtailcore.Page',
        on_delete=models.PROTECT,
        related_name='+',
        verbose_name=_lazy('target page'),
    )

    panels = [
        FieldPanel('category'),
        FieldPanel('inherit'),
        PageChooserPanel('target'),
    ]

    def __str__(self):
        return f'{self.category.title}: {self.target.title}'
