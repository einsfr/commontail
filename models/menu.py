from typing import Iterable, Any, Optional

from django.conf import settings
from django.utils.translation import gettext_lazy as _

from wagtail.admin.edit_handlers import FieldPanel, StreamFieldPanel
from wagtail.core import blocks
from wagtail.core.fields import StreamField

from ..blocks import DocumentLinkBlock, ExternalLinkBlock, PageLinkBlock

from .cache import AbstractCacheAware, CacheMeta
from .utils import AbstractSiteHandleModel


__all__ = ['MenuSubcategoryItemsBlock', 'MenuSubcategoryBlock', 'MenuCategoryItemsBlock', 'MenuCategoryBlock',
           'AbstractMenu', 'Menu']


def _get_templates_list(base_name: str, context=None) -> list[str]:
    templates_list: list[str] = []

    template_name: Optional[str] = context.get('template_name', None)
    if template_name:
        templates_list.append(f'commontail/menu/{base_name}.{template_name}.html')

    try:
        handle: str = context['instance'].handle
    except (KeyError, TypeError):
        pass
    else:
        templates_list.append(f'commontail/menu/{base_name}.{handle}.html')

    templates_list.append(f'commontail/menu/{base_name}.html')

    return templates_list


class MenuSubcategoryItemsBlock(blocks.StreamBlock):

    class Meta:
        icon = 'list-ul'
        label = _('Menu subcategory items')

    document = DocumentLinkBlock()

    external = ExternalLinkBlock()

    page = PageLinkBlock()


class MenuSubcategoryBlock(blocks.StructBlock):

    class Meta:
        icon = 'list-ul'
        label = _('Menu subcategory')
        template = 'commontail/menu/menu_subcategory.html'

    title = blocks.CharBlock(required=True, max_length=64, label=_('Menu subcategory title'))

    items = MenuSubcategoryItemsBlock()

    def get_template(self, context=None):
        return _get_templates_list('menu_subcategory', context)


class MenuCategoryItemsBlock(MenuSubcategoryItemsBlock):

    class Meta:
        icon = 'list-ul'
        label = _('Menu category items')

    subcategory = MenuSubcategoryBlock()


class MenuCategoryBlock(blocks.StructBlock):

    class Meta:
        icon = 'list-ul'
        label = _('Menu category')
        template = 'commontail/menu/menu_category.html'

    title = blocks.CharBlock(required=True, max_length=64, label=_('Menu category title'))

    items = MenuCategoryItemsBlock()

    def get_template(self, context=None):
        return _get_templates_list('menu_category', context)


class AbstractMenu(AbstractCacheAware, AbstractSiteHandleModel):

    class Meta(AbstractSiteHandleModel.Meta):
        abstract = True
        verbose_name = 'меню'
        verbose_name_plural = 'меню'

    items = StreamField(
        [
            ('category', MenuCategoryBlock()),
            ('document', DocumentLinkBlock()),
            ('external', ExternalLinkBlock()),
            ('page', PageLinkBlock()),
        ],
        verbose_name=_('Menu items')
    )

    cache_template_prefix = 'menu_template'

    cache_prefixes = AbstractCacheAware.cache_prefixes + {
        cache_template_prefix: CacheMeta(
            ('template_fragments', 'default'),
            settings.COMMONTAIL_MENU_CACHE_LIFETIME
        )
    }

    panels = [
        FieldPanel('site'),
        FieldPanel('handle'),
        StreamFieldPanel('items'),
    ]

    def __str__(self):
        return self.handle

    def get_cache_vary_on(self) -> Iterable[Any]:
        return self.site_id, self.handle


class Menu(AbstractMenu):
    pass
