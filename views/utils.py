from django.conf import settings
from django.contrib.staticfiles import finders
from django.http.request import HttpRequest
from django.http.response import FileResponse


__all__ = ['favicon', ]


def favicon(request: HttpRequest) -> FileResponse:
    return FileResponse(open(finders.find(settings.COMMONTAIL_FAVICON_ICO_STATIC_PATH), 'rb'))
