from collections import OrderedDict
from typing import Optional, List, Iterable, Union, Tuple

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from modelcluster.models import ClusterableModel, ParentalKey

from wagtail.admin.edit_handlers import FieldPanel, PageChooserPanel, InlinePanel
from wagtail.core.models import Orderable, Page
from wagtail.documents.edit_handlers import DocumentChooserPanel
from wagtail.images import get_image_model_string
from wagtail.images.edit_handlers import ImageChooserPanel

from .utils import AbstractIconAware


__all__ = ['AbstractPageLink', 'BaseLinksCollector', 'AbstractBaseLinkFields', 'AbstractLinkedDocument',
           'AbstractLinkedImage', 'AbstractLinkFields', 'AbstractLinksOwnerPage', 'PageLinkCategory',
           'PageLinkCategoryGroup', 'PageLinkCategoryToPageLinkCategoryGroup', 'PageLinksCollector', ]


class AbstractBaseLinkFields(models.Model):

    class Meta:
        abstract = True

    email = models.EmailField(
        verbose_name=_('e-mail address'),
        blank=True,
        help_text=_('E-mail address to be used as a link.')
    )

    link_document = models.ForeignKey(
        'wagtaildocs.Document',
        verbose_name=_('link to a document'),
        null=True,
        blank=True,
        related_name='+',
        on_delete=models.CASCADE,
        help_text=_('Link to a document on this site.')
    )

    link_external = models.URLField(
        verbose_name=_('external link'),
        blank=True,
        help_text='Link to external URL. Must be used with "Link\'s test" field.'
    )

    link_page = models.ForeignKey(
        'wagtailcore.Page',
        verbose_name=_('link to a page'),
        null=True,
        blank=True,
        related_name='+',
        on_delete=models.CASCADE,
        help_text=_('Link to a page on this site. "Query string" field may be used.')
    )

    query_string = models.CharField(
        max_length=255,
        verbose_name=_('query string for a page link'),
        blank=True,
        help_text=_('Query string parameters without opening ?.')
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


class AbstractLinkFields(AbstractBaseLinkFields):  # https://github.com/wagtail/wagtaildemo/blob/master/demo/models.py

    class Meta:
        abstract = True

    link_text = models.CharField(
        verbose_name=_('link\'s text'),
        blank=True,
        max_length=255,
        help_text=_('Link\'s text. Required for external links only. '
                        'May be used as substitute text with page and document links.')
    )

    panels = AbstractBaseLinkFields.panels + [
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


class AbstractLinkedDocument(models.Model):

    class Meta:
        abstract = True
        verbose_name = _('linked document')
        verbose_name_plural = _('linked documents')

    document = models.ForeignKey(
        'wagtaildocs.Document',
        verbose_name=_('document'),
        related_name='+',
        on_delete=models.CASCADE,
        help_text=_('Document on this site.')
    )

    inherit = models.BooleanField(
        verbose_name=_('allow inheritance'),
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


class AbstractLinkedImage(Orderable):

    class Meta(Orderable.Meta):
        abstract = True
        verbose_name = _('linked image')
        verbose_name_plural = _('linked_images')

    image = models.ForeignKey(
        get_image_model_string(),
        verbose_name=_('image'),
        related_name='+',
        on_delete=models.CASCADE,
        help_text=_('Image on this site.')
    )

    inherit = models.BooleanField(
        verbose_name=_('allow inheritance'),
        default=True,
    )

    panels = [
        ImageChooserPanel('image'),
        FieldPanel('inherit'),
    ]


class PageLinkCategory(models.Model):

    class Meta:
        verbose_name = _('category of a page-to-page link')
        verbose_name_plural = _('categories of page-to-page links')

    title = models.CharField(
        verbose_name=_('title'),
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
                handle=settings.COMMONTAIL_PAGE_LINKS_CATEGORIES_GROUP_DEFAULT_HANDLE)
            max_order: int = group.category_relations.aggregate(models.Max('sort_order'))['sort_order__max']

            PageLinkCategoryToPageLinkCategoryGroup.objects.create(
                category=self,
                group=group,
                sort_order=max_order + 1,
            )


class PageLinkCategoryGroup(ClusterableModel):

    class Meta:
        verbose_name = _('page-to-page link categories group')
        verbose_name_plural = _('page-to-page link categories groups')

    title = models.CharField(
        verbose_name=_('title'),
        max_length=255,
    )

    handle = models.CharField(
        verbose_name=_('handle'),
        max_length=255,
        unique=True,
    )

    panels = [
        FieldPanel('title'),
        FieldPanel('handle'),
        InlinePanel('category_relations', label=_('Categories')),
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
        verbose_name=_('category'),
    )

    group = ParentalKey(
        PageLinkCategoryGroup,
        on_delete=models.CASCADE,
        related_name='category_relations',
        verbose_name=_('group'),
    )

    panels = [
        FieldPanel('category'),
    ]


class AbstractPageLink(Orderable):

    class Meta(Orderable.Meta):
        abstract = True
        verbose_name = _('page-to-page link')
        verbose_name_plural = _('page-to-page links')

    category = models.ForeignKey(
        PageLinkCategory,
        on_delete=models.PROTECT,
        related_name='+',
        verbose_name=_('category'),
    )

    inherit = models.BooleanField(
        verbose_name=_('allow inheritance'),
        default=True,
    )

    target = models.ForeignKey(
        'wagtailcore.Page',
        on_delete=models.PROTECT,
        related_name='+',
        verbose_name=_('target page'),
    )

    panels = [
        FieldPanel('category'),
        FieldPanel('inherit'),
        PageChooserPanel('target'),
    ]

    def __str__(self):
        return f'{self.category.title}: {self.target.title}'


class BaseLinksCollector:

    collect_sources: List[str] = ['self', ]

    source_excludes: dict = dict()

    source_filters: dict = dict()

    def __init__(self, obj: object, relation_name: str, id_field: str = None, count: int = None, **kwargs):
        self._obj: object = obj
        self._relation_name: str = relation_name
        self._id_field: Optional[str] = id_field
        self._count: Optional[int] = count

    @staticmethod
    def _apply_filters_excludes(qs: models.QuerySet, filters: dict, excludes: dict) -> models.QuerySet:
        if filters:
            qs = qs.filter(**filters)
        if excludes:
            qs = qs.exclude(**excludes)

        return qs

    def _create_collect_qs(self, o: object, collected_ids: list, filters: dict, excludes: dict,
                           select_related: Iterable) -> models.QuerySet:
        qs: models.QuerySet = getattr(o, self._relation_name).all()
        if select_related:
            qs = qs.select_related(*select_related)
        if collected_ids:
            qs = qs.exclude(**{f'{self._id_field}__in': collected_ids})

        return self._apply_filters_excludes(qs, filters, excludes)

    def collect(self, flat: bool = True, filters: dict = None, excludes: dict = None,
                select_related: Union[str, Iterable] = None) -> Union[dict, list]:

        def _flatten_result(result: OrderedDict) -> Union[OrderedDict, List]:
            if flat:
                return [i for sl in result.values() for i in sl]
            else:
                return result

        if self._id_field is None:
            raise ValueError('To use "collect" method class instance must be created with non-empty '
                             '"id_field" parameter.')

        if select_related and type(select_related) == str:
            select_related = [select_related]

        collected_dict = OrderedDict()
        collected_ids = []

        for source in self.collect_sources:
            source_list = getattr(self, f'collect_from_{source}')(
                collected_ids=collected_ids,
                filters=self.source_filters.get(source, None) if not filters else {
                    **self.source_filters.get(source, dict()),
                    **filters
                },
                excludes=self.source_excludes.get(source, None) if not excludes else {
                    **self.source_excludes.get(source, dict()),
                    **excludes
                },
                select_related=select_related
            )
            if self._count and (len(collected_ids) + len(source_list)) >= self._count:
                collected_dict[source] = source_list[:self._count - len(collected_ids)]

                return _flatten_result(collected_dict)

            collected_ids.extend((getattr(i, self._id_field) for i in source_list))
            collected_dict[source] = source_list

        return _flatten_result(collected_dict)

    def collect_from_self(self, collected_ids: list, filters: dict, excludes: dict, select_related: Iterable) -> list:
        return self.collect_generic(self._obj, collected_ids, filters, excludes, select_related)

    def collect_generic(self, o: object, collected_ids: list, filters: dict, excludes: dict,
                        select_related: Iterable) -> list:
        if hasattr(0, self._relation_name):
            return list(self._create_collect_qs(o, collected_ids, filters, excludes, select_related))
        else:
            return []

    def collect_generic_multiple(self, o_list: list, collected_ids: list, filters: dict, excludes: dict,
                                 select_related: Iterable) -> list:
        current_collected_ids: list = []
        result: list = []

        for c in filter(lambda x: hasattr(x, self._relation_name), o_list):
            c_list = list(self._create_collect_qs(c, collected_ids + current_collected_ids, filters, excludes,
                                                  select_related))
            result.extend(c_list)

            if self._count and (len(collected_ids) + len(result)) >= self._count:
                return result

            current_collected_ids.extend((getattr(i, self._id_field) for i in c_list))

        return result

    def exists(self, filters: dict = None, excludes: dict = None) -> bool:
        return any((getattr(self, f'exists_in_{source}')(
            filters=self.source_filters.get(source, None) if not filters else {
                **self.source_filters.get(source, dict()),
                **filters
            },
            excludes=self.source_excludes.get(source, None) if not excludes else {
                **self.source_excludes.get(source, dict()),
                **excludes
            },
        ) for source in self.collect_sources))

    def exists_generic(self, o: object, filters: dict, excludes: dict):
        return self._apply_filters_excludes(getattr(o, self._relation_name), filters, excludes).exists()

    def exists_generic_multiple(self, o_list: list, filters: dict, excludes: dict) -> bool:
        return any((
            hasattr(o, self._relation_name) and self.exists_generic(o, filters, excludes)
            for o in o_list
        ))

    def exists_in_self(self, filters: dict, excludes: dict) -> bool:
        return hasattr(self._obj, self._relation_name) and self.exists_generic(self._obj, filters, excludes)


class PageLinksCollector(BaseLinksCollector):

    collect_sources = BaseLinksCollector.collect_sources + ['ancestors', 'descendants']

    source_filters = {
        'ancestors': {'inherit': True},
    }

    def __init__(self, obj: 'AbstractLinksOwnerPage', relation_name: str, id_field: str = None, count: int = None,
                 include_descendants: bool = False, ancestors_depth: Optional[int] = 2, **kwargs):

        super().__init__(obj, relation_name, id_field, count)
        self._include_descendants = include_descendants
        self._ancestors_depth = ancestors_depth

    def _get_ancestors_qs(self):
        return Page.objects.live().ancestor_of(self._obj).type(AbstractLinksOwnerPage).specific()

    def _get_descendants_qs(self):
        return Page.objects.live().descendant_of(self._obj).type(AbstractLinksOwnerPage).specific()

    def collect_from_ancestors(self, collected_ids: list, filters: dict, excludes: dict,
                               select_related: Iterable) -> list:
        if self._ancestors_depth is None:
            return []
        ancestors = self._get_ancestors_qs()

        return self.collect_generic_multiple(
            ancestors if not self._ancestors_depth else ancestors.reverse()[:self._ancestors_depth],
            collected_ids, filters, excludes, select_related
        )

    def collect_from_descendants(self, collected_ids: list, filters: dict, excludes: dict,
                                 select_related: Iterable) -> list:
        if not self._include_descendants:
            return []
        descendants = self._get_descendants_qs()

        return self.collect_generic_multiple(descendants, collected_ids, filters, excludes, select_related)

    def exists_in_ancestors(self, filters: dict, excludes: dict) -> bool:
        if self._ancestors_depth is None:
            return False

        return self.exists_generic_multiple(self._get_ancestors_qs(), filters, excludes)

    def exists_in_descendants(self, filters: dict, excludes: dict) -> bool:
        if not self._include_descendants:
            return False

        return self.exists_generic_multiple(self._get_descendants_qs(), filters, excludes)


class AbstractLinksOwnerPage(Page):

    class Meta:
        abstract = True

    links_collector_class = PageLinksCollector

    @staticmethod
    def _get_linked_page_filters(handle: Union[PageLinkCategoryGroup, str, None], filters: Optional[dict],
                                 live_only: bool) -> Tuple[PageLinkCategoryGroup, dict]:
        if isinstance(handle, PageLinkCategoryGroup):
            group = handle
        else:
            if handle is None:
                handle = settings.COMMONTAIL_PAGE_LINKS_CATEGORIES_GROUP_DEFAULT_HANDLE
            try:
                group = PageLinkCategoryGroup.objects.get(handle=handle)
            except PageLinkCategoryGroup.DoesNotExist:
                raise ValueError(f'Unknown link category group with "{handle}" handle.')

        categories_ids = group.category_relations.all().values_list('category_id', flat=True)
        result = {'category_id__in': categories_ids} if not filters else {
            **filters,
            'category_id__in': categories_ids,
        }

        if live_only:
            result['target__live'] = True

        return group, result

    def get_linked_items(self, relation_name: str, id_field: str, count: int = None, flat: bool = True,
                         filters: dict = None, excludes: dict = None, select_related: Union[str, Iterable] = None,
                         include_descendants: bool = False, ancestors_depth: Optional[int] = 3,
                         **kwargs) -> Union[dict, list]:
        return self.links_collector_class(
            self, relation_name=relation_name, id_field=id_field, count=count, include_descendants=include_descendants,
            ancestors_depth=ancestors_depth, **kwargs
        ).collect(flat, filters=filters, excludes=excludes, select_related=select_related)

    def get_linked_pages(self, handle: Union[PageLinkCategoryGroup, str] = None, count: int = None, flat: bool = True,
                         filters: dict = None,
                         excludes: dict = None, select_related: Union[str, Iterable] = None, live_only: bool = True,
                         group: bool = False, include_descendants: bool = False,
                         ancestors_depth: Optional[int] = 3, **kwargs) -> Union[dict, list]:
        categories_group, linked_page_filters = self._get_linked_page_filters(handle, filters, live_only)

        if select_related is None:
            select_related = 'target'

        collected_links = self.links_collector_class(
            self, relation_name=settings.COMMONTAIL_PAGE_LINKS_RELATION_NAME, id_field='target_id', count=count,
            include_descendants=include_descendants, ancestors_depth=ancestors_depth, **kwargs
        ).collect(
            flat if not group else True, filters=linked_page_filters,
            excludes=excludes, select_related=select_related
        )

        if not group:
            return collected_links

        categories = categories_group.category_relations.all().select_related('category').values(
            'category__pk', 'category__title')

        categories_map = {cr['category__pk']: cr['category__title'] for cr in categories}

        result = OrderedDict(((cr['category__title'], []) for cr in categories))

        for cl in collected_links:
            result[categories_map[cl.category_id]].append(cl)

        for key in [k for k in result.keys()]:
            if not result[key]:
                result.pop(key, None)

        return result

    def has_linked_items(self, relation_name: str, filters: dict = None, excludes: dict = None,
                         include_descendants: bool = False, ancestors_depth: Optional[int] = 3, **kwargs) -> bool:
        return self.links_collector_class(
            self, relation_name=relation_name, include_descendants=include_descendants, ancestors_depth=ancestors_depth,
            **kwargs
        ).exists(filters=filters, excludes=excludes)

    def has_linked_pages(self, handle: Union[PageLinkCategoryGroup, str] = None, filters: dict = None,
                         excludes: dict = None, live_only: bool = True, include_descendants: bool = False,
                         ancestors_depth: Optional[int] = 3, **kwargs) -> bool:
        _, linked_page_filters = self._get_linked_page_filters(handle, filters, live_only)

        return self.links_collector_class(
            self, relation_name=settings.COMMONTAIL_PAGE_LINKS_RELATION_NAME, include_descendants=include_descendants,
            ancestors_depth=ancestors_depth, **kwargs
        ).exists(
            filters=linked_page_filters,
            excludes=excludes
        )
