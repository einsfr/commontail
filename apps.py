from django.apps import AppConfig


class CommonConfig(AppConfig):
    default_auto_field = 'django.db.models.AutoField'
    name = 'commontail'

    def ready(self):
        from commontail.signals import register_cache_aware_signal_handlers

        register_cache_aware_signal_handlers()
