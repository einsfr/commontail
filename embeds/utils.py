import re

from typing import List, Optional

from django.conf import settings


__all__ = ['url_matches_allowed_pattern', ]


_compiled_re: Optional[List[re.Pattern]] = None


def url_matches_allowed_pattern(url: str) -> bool:
    global _compiled_re

    if _compiled_re is None:
        _compiled_re = []

        if settings.COMMONTAIL_EMBED_PLAYER_URL_PATTERNS:
            for url_pattern in settings.COMMONTAIL_EMBED_PLAYER_URL_PATTERNS:
                _compiled_re.append(re.compile(url_pattern))

    return not _compiled_re or any((re.match(pattern, url) for pattern in _compiled_re))
