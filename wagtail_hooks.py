from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register

from .models import Menu


class MenuModelAdmin(ModelAdmin):

    list_display = ('site', 'handle')
    list_filter = ('site', )
    menu_icon = 'list-ul'
    model = Menu


modeladmin_register(MenuModelAdmin)
