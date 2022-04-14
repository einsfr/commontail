from django.apps import AppConfig, apps
from django.conf import settings

from wagtailmodelchooser import registry


class CommonConfig(AppConfig):
    default_auto_field = 'django.db.models.AutoField'
    name = 'commontail'

    def ready(self):
        from commontail.signals import register_cache_aware_signal_handlers

        register_cache_aware_signal_handlers()

        registry.register_chooser(apps.get_model(*settings.AUTH_USER_MODEL.split('.')))
        registry.register_chooser(apps.get_model('commontail', 'Author'))
