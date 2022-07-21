from typing import Iterable, Optional

from wagtail.core import hooks

from .models import *
from .abstract import *
from .spreadsheet import *


_exporters: Optional[Iterable] = None
_importers: Optional[Iterable] = None


def get_importers() -> Iterable:
    global _importers

    if _importers is None:
        _importers = sorted((h() for h in hooks.get_hooks('commontail_register_importer')), key=lambda x: x.title)

    return _importers


def get_importer_by_url_suffix(url_suffix):
    for i in get_importers():
        if i.url_suffix == url_suffix:
            return i


def get_exporters() -> Iterable:
    global _exporters

    if _exporters is None:
        _exporters = sorted((h() for h in hooks.get_hooks('commontail_register_exporter')), key=lambda x: x.title)

    return _exporters


def get_exporter_by_url_suffix(url_suffix):
    for e in get_exporters():
        if e.url_suffix == url_suffix:
            return e
