from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import models


__all__ = ['GlobalPermission', 'GlobalPermissionManager', ]


class GlobalPermissionManager(models.Manager):

    def get_queryset(self):
        return super().get_queryset().filter(content_type__models='global_permission')


class GlobalPermission(Permission):

    class Meta:
        proxy = True

    objects = GlobalPermissionManager()

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        content_type: ContentType
        content_type, _ = ContentType.objects.get_or_create(
            model='global_permission', app_label='commontail'
        )
        self.content_type = content_type

        super().save(force_insert=False, force_update=False, using=None,
                     update_fields=None)
