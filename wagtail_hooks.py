from django.contrib.auth.models import Permission
from django.urls import reverse, path, include
from django.utils.translation import gettext_lazy as _

from wagtail.admin.menu import MenuItem
from wagtail.admin.action_menu import ActionMenuItem
from wagtail.contrib.modeladmin.options import ModelAdmin, ModelAdminGroup, modeladmin_register
from wagtail.core import hooks

from .models import Menu, PageViewsCounter, AbstractViewsCountablePage, Author, AuthorHomePageRelation,\
    AbstractCacheAwarePage
    # Banner, BannerSet, Hint
from .urls import admin_urls


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        path('commontail/', include((admin_urls, 'commontail_admin')))
    ]


class MenuModelAdmin(ModelAdmin):

    list_display = ('site', 'handle')
    list_filter = ('site', )
    menu_icon = 'list-ul'
    model = Menu


modeladmin_register(MenuModelAdmin)


class AuthorModelAdmin(ModelAdmin):

    list_display = ('first_name', 'last_name', 'email', 'user')
    menu_icon = 'user'
    model = Author


class AuthorHomePageAdmin(ModelAdmin):

    list_display = ('site', 'author', 'page')
    menu_icon = 'home'
    model = AuthorHomePageRelation


class PublicationModelAdminGroup(ModelAdminGroup):

    menu_label = _('Publications')
    menu_icon = 'doc-full'
    items = [AuthorModelAdmin, AuthorHomePageAdmin, ]


modeladmin_register(PublicationModelAdminGroup)


def create_views_counter(request, page):
    if isinstance(page, AbstractViewsCountablePage):
        PageViewsCounter.objects.get_or_create(page_id=page.pk, defaults={'views_count': 0})


hooks.register('after_create_page', lambda request, page: create_views_counter(request, page))
hooks.register('after_copy_page', lambda request, page, new_page: create_views_counter(request, new_page))


class ClearCacheMenuItem(ActionMenuItem):
    icon_name = 'bin'
    label = _('Clear cache')
    name = 'action-clear-cache'

    def get_url(self, context):
        return reverse('commontail_admin:clear_cache', kwargs={'page_id': context['page'].id})

    def is_shown(self, context):
        if context['view'] == 'edit' and isinstance(context['page'], AbstractCacheAwarePage) \
                and self.get_user_page_permissions_tester(context).can_edit():
            return True


@hooks.register('register_page_action_menu_item')
def register_clear_cache_menu_item():
    return ClearCacheMenuItem()


# class BannerSetModelAdmin(ModelAdmin):
#
#     model = BannerSet
#     list_display = ('title', 'handle', )
#
#
# class BannerModelAdmin(ModelAdmin):
#
#     model = Banner
#
#
# class BannerModelAdminGroup(ModelAdminGroup):
#
#     menu_label = _('Banners')
#     menu_icon = 'image'
#     items = [BannerSetModelAdmin, BannerModelAdmin, ]
#
#
# modeladmin_register(BannerModelAdminGroup)
#
#
# class HintModelAdmin(ModelAdmin):
#
#     model = Hint
#     list_display = ('title', 'handle', )
#
#
# class HintModelAdminGroup(ModelAdminGroup):
#
#     menu_label = _('Hints')
#     menu_icon = 'help'
#     items = [HintModelAdmin, ]
#
#
# modeladmin_register(HintModelAdminGroup)


@hooks.register('register_permissions')
def register_global_permissions():
    return Permission.objects.filter(content_type__model='global_permission')


@hooks.register('register_admin_menu_item')
def register_import_menu_item():
    return MenuItem(_('Import'), reverse('commontail_admin:import_index'), classnames='icon icon-collapse-up',
                    order=11000)


@hooks.register('register_admin_menu_item')
def register_export_menu_item():
    return MenuItem(_('Export'), reverse('commontail_admin:export_index'), classnames='icon icon-collapse-down',
                    order=11001)
