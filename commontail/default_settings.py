from typing import List, Tuple

COMMONTAIL_CONTENT_STREAM_PAGE_BODY_BLOCK: str = 'commontail.blocks.ContentStreamBlock'

COMMONTAIL_LINK_ICON_DOCUMENT_DEFAULT = 'far fa-file'
COMMONTAIL_LINK_ICON_EXTERNAL = 'fas fa-globe'

COMMONTAIL_NAMED_URL_CACHE_KEY_PREFIX: str = 'named_url_'
COMMONTAIL_NAMED_URL_CACHE_LIFETIME: int = 3600
COMMONTAIL_NAMED_URL_SUPPRESS_NOT_FOUND_EXCEPTION: bool = False

COMMONTAIL_NO_IMAGE_PLACEHOLDER_TITLE: str = '__IMAGE_LATER__'

COMMONTAIL_OPENGRAPH_CACHE_LIFETIME: int = 86400

COMMONTAIL_PAGE_LINKS_CATEGORIES_GROUP_DEFAULT_HANDLE: str = 'all'
COMMONTAIL_PAGE_LINKS_RELATION_NAME: str = 'page_links'

COMMONTAIL_PAGINATION_NEIGHBOURS_COUNT: int = 2

COMMONTAIL_RTF_INLINE_FEATURES: List[str] = ['bold', 'italic', 'link', 'document-link', 'superscript', 'subscript',
                                             'strikethrough', ]
COMMONTAIL_RTF_LIMITED_FEATURES: List[str] = COMMONTAIL_RTF_INLINE_FEATURES + ['ol', 'ul', ]
COMMONTAIL_RTF_NO_IMAGE_EMBED_FEATURES: List[str] = COMMONTAIL_RTF_LIMITED_FEATURES + ['h4', 'h5', 'h6', ]
COMMONTAIL_RTF_BASIC_FEATURES: List[str] = COMMONTAIL_RTF_NO_IMAGE_EMBED_FEATURES + ['image', 'embed', ]

COMMONTAIL_SITEMAP_DEFAULT_INCLUDE: bool = True
COMMONTAIL_SITEMAP_DEFAULT_ALLOW_INDEXING: bool = True
COMMONTAIL_SITEMAP_DEFAULTS: Tuple[str, float] = ('weekly', 0.5)

COMMONTAIL_SOCIAL_LINKS_OPEN_IN_NEW_WINDOW: bool = True

COMMONTAIL_STRUCTURED_DATA_CACHE_LIFETIME: int = 86400
