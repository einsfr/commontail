from django.conf import settings
from django.views.generic import TemplateView

from wagtail.models import Site

__all__ = ['RobotsTxtView', ]


class RobotsTxtView(TemplateView):

    content_type = 'text/plain'
    template_name = 'commontail/robots.txt'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['settings'] = settings
        context['root_url'] = Site.find_for_request(self.request).root_url

        return context
