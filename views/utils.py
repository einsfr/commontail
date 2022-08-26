import os.path
from typing import Union

from django.conf import settings
from django.contrib.staticfiles import finders
from django.http.request import HttpRequest
from django.http.response import FileResponse, HttpResponseNotFound


__all__ = ['favicon', ]


def favicon(request: HttpRequest) -> Union[FileResponse, HttpResponseNotFound]:
    path = finders.find(settings.COMMONTAIL_FAVICON_ICO_STATIC_PATH)

    if path and os.path.exists(path):
        return FileResponse(open(path, 'rb'))
    else:
        return HttpResponseNotFound()
