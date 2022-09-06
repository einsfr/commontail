from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.http.response import HttpResponseBadRequest
from django.views.generic import TemplateView

from .utils import url_matches_allowed_pattern


__all__ = ['PlayerEmbedView', ]


class PlayerEmbedView(TemplateView):

    template_name = 'commontail/embeds/player.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        if not context.get('url', None):
            return HttpResponseBadRequest()

        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if 'url' in self.request.GET:
            url: str = self.request.GET['url']

            try:
                URLValidator(schemes=['http', 'https'])(url)
            except ValidationError:
                pass
            else:
                if url_matches_allowed_pattern(url):
                    context['url'] = url

        return context
