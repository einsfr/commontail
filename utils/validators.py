from math import isclose
from typing import List, Optional

from django.core.validators import ValidationError
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _

from wagtail.images.models import Image


__all__ = ['ImageSizeValidator', ]


@deconstructible
class ImageSizeValidator:

    def __init__(self, min_width: Optional[int] = None, min_height: Optional[int] = None,
                 max_width: Optional[int] = None, max_height: Optional[int] = None,
                 ratio: Optional[float] = None, ratio_abs_tol: Optional[float] = None):
        self.min_width: Optional[int] = min_width
        self.min_height: Optional[int] = min_height
        self.max_width: Optional[int] = max_width
        self.max_height: Optional[int] = max_height
        self.ratio: Optional[float] = ratio
        self.ratio_abs_tol: float = ratio_abs_tol if ratio_abs_tol else 1e-03

    def __call__(self, image: Image):
        if not image:
            return

        msg: List[str] = []

        if self.min_width is not None and image.width < self.min_width:
            msg.append(_('Image width must not be less than %d pixels.') % self.min_width)
        if self.max_width is not None and image.width > self.max_width:
            msg.append(_('Image width must not be greater than %d pixels.') % self.max_width)
        if self.min_height is not None and image.height < self.min_height:
            msg.append(_('Image height must not be less than %d pixels.') % self.min_height)
        if self.max_height is not None and image.height > self.max_height:
            msg.append(_('Image height must not be greater than %d pixels.') % self.max_height)
        if self.ratio is not None:
            if not isclose(image.width / image.height, self.ratio, abs_tol=self.ratio_abs_tol):
                msg.append(_('Image ratio must be close to %.3f.') % self.ratio)

        if msg:
            raise ValidationError(' '.join(msg))

    def __eq__(self, other):
        return (
            isinstance(other, ImageSizeValidator) and
            self.min_width == other.min_width and
            self.min_height == other.min_height and
            self.max_width == other.max_width and
            self.max_height == other.max_height and
            self.ratio == other.ratio and
            self.ratio_abs_tol == other.ratio_abs_tol
        )
