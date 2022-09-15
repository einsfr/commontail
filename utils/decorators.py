from functools import wraps

from django.http.request import HttpRequest
from django.http.response import HttpResponseBadRequest


__all__ = ['ajax_only', ]


def ajax_only(f):

    @wraps(f)
    def wrap(request: HttpRequest, *args, **kwargs):
        if not request.is_ajax():
            return HttpResponseBadRequest('AJAX only.')

        return f(request, *args, **kwargs)

    return wrap
