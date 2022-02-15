import importlib

from typing import List, Type

from django.conf import settings

from wagtail.core.blocks import StreamBlock


__all__ = ['get_content_stream_page_body_block', ]


def get_content_stream_page_body_block(**kwargs) -> StreamBlock:
    import_parts: List[str] = settings.COMMONTAIL_CONTENT_STREAM_PAGE_BODY_BLOCK.split('.')
    module_name: str = '.'.join(import_parts[:-1])
    body_block: Type[StreamBlock] = getattr(importlib.import_module(module_name), import_parts[-1])

    return body_block(**kwargs)
