from django.http.request import HttpRequest
from django.shortcuts import render


__all__ = ['page404', 'page500', ]


def page404(request: HttpRequest):
    return render(request, '404.html', status=404)


def page500(request: HttpRequest):
    return render(request, '500.html', status=500)
