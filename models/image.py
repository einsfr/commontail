from typing import Optional

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from wagtail.images.models import Image as WagtailImage


__all__ = ['Image', ]


class Image(WagtailImage):
    """
    Proxy model for wagtail image with placeholder logic
    """

    class Meta:
        proxy = True

    @classmethod
    def get_no_image_placeholder(cls) -> Optional['Image']:
        try:
            return cls.objects.get(title=settings.COMMONTAIL_NO_IMAGE_PLACEHOLDER_TITLE)
        except ObjectDoesNotExist:
            return None

    def is_no_image_placeholder(self) -> bool:
        return self.title == settings.COMMONTAIL_NO_IMAGE_PLACEHOLDER_TITLE
