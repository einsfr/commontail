from django import template
from django.conf import settings
from django.template.loader import select_template

from wagtail.core.models import Site

from ..models import Menu


register = template.Library()


class MenuNode(template.Node):

    def __init__(self, handle: str):
        self._handle = template.Variable(handle)

    def render(self, context):
        handle: str = self._handle.resolve(context)

        try:
            site: Site = Site.find_for_request(context['request'])
        except Site.DoesNotExist as e:
            if settings.DEBUG:
                raise e
            else:
                return ''

        rendered_content: str = Menu.get_cache_data(Menu.TEMPLATE_CACHE_PREFIX, (site, handle, ))
        if rendered_content is not None:
            return rendered_content

        try:
            menu_obj: Menu = Menu.objects.get(site=site, handle=handle)
        except Menu.DoesNotExist as e:
            if settings.DEBUG:
                raise e
            else:
                return ''

        t: template.Template = select_template([
            f'commontail/menu/menu.{handle}.html',
            'commontail/menu/menu.html'
        ])

        rendered_content: str = t.render({
            'menu': menu_obj,
        })

        Menu.set_cache_data(Menu.TEMPLATE_CACHE_PREFIX, rendered_content, (site, handle, ))

        return rendered_content


@register.tag
def build_menu(parser, token):
    tag_name: str
    handle: str
    try:
        tag_name, handle = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(f'{token.contents.split()[0]} tag takes one argument - menu handle.')

    return MenuNode(handle)
