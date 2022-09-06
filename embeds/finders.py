from urllib.parse import quote_plus
from requests import head, Response

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

from wagtail.embeds.exceptions import EmbedNotFoundException
from wagtail.embeds.finders.base import EmbedFinder

from .utils import url_matches_allowed_pattern

__all__ = ['PlayerEmbedFinder', ]


class PlayerEmbedFinder(EmbedFinder):

    def accept(self, url):
        try:
            URLValidator(schemes=['http', 'https'])(url)
        except ValidationError:
            return False
        else:
            return url_matches_allowed_pattern(url)

    def find_embed(self, url, max_width=None, max_height=None):
        if not url_matches_allowed_pattern(url):
            return EmbedNotFoundException

        response: Response = head(url)
        if response.status_code != 200 or 'Content-Type' not in response.headers \
                or response.headers['Content-Type'] not in settings.COMMONTAIL_EMBED_PLAYER_CONTENT_TYPES:
            raise EmbedNotFoundException

        ratio: float = 1.777778  # 16/9
        width: int
        height: int

        if max_width:
            if max_height:
                if max_width / max_height > ratio:
                    width = max_width
                    height = int(max_width / ratio)
                else:
                    width = int(max_height * ratio)
                    height = max_height
            else:
                width = max_width
                height = int(max_width / ratio)
        else:
            if max_height:
                width = int(max_height * ratio)
                height = max_height
            else:
                width = 640
                height = 360

        return {
            'title': '',
            'author_name': '',
            'provider_name': 'Direct URL',
            'type': 'video',
            'thumbnail_url': '',
            'width': width,
            'height': height,
            'html': f'<iframe width="{width}" height="{height}" '
                    f'src="/{settings.COMMONTAIL_URL_API_PREFIX}'
                    f'{settings.COMMONTAIL_URL_API_EMBED}?url={quote_plus(url)}" '
                    f'frameborder="0" allowfullscreen title=""></iframe>',
        }
