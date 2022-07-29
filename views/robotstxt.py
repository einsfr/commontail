from django.conf import settings
from django.views.generic import TemplateView

from wagtail.core.models import Site

__all__ = ['RobotsTxtView', ]


class RobotsTxtView(TemplateView):

    template_name = 'commontail/robots.txt'

    def render_to_response(self, context, **response_kwargs):
        context['settings'] = settings
        context['root_url'] = Site.find_for_request(context['request']).root_url

        return super().render_to_response(context, content_type='text/plain', **response_kwargs)
