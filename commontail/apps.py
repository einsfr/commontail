from django.apps import AppConfig


class CommonConfig(AppConfig):
    name = 'commontail'

    def ready(self):
        from commontail.signals import register_cache_aware_signal_handlers

        register_cache_aware_signal_handlers()
