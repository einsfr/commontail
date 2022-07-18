from typing import Optional

from django import template
from django.conf import settings
from django.template.loader import select_template

from wagtail.core.models import Site

from ..models import Menu


register = template.Library()


class MenuNode(template.Node):

    def __init__(self, handle: str, template_name: Optional[str]):
        self._handle = template.Variable(handle)
        self._template_name = template.Variable(template_name) if template_name else None

    def render(self, context):
        handle: str = self._handle.resolve(context)
        template_name: Optional[str] = self._template_name.resolve(context) if self._template_name else None

        try:
            site: Site = Site.find_for_request(context['request'])
        except Site.DoesNotExist as e:
            if settings.DEBUG:
                raise e
            else:
                return ''

        if template_name:
            rendered_content: str = Menu.get_cache_data(Menu.TEMPLATE_CACHE_PREFIX, (site, handle, template_name, ))
        else:
            rendered_content: str = Menu.get_cache_data(Menu.TEMPLATE_CACHE_PREFIX, (site, handle,))
        if rendered_content is not None:
            return rendered_content

        try:
            menu_obj: Menu = Menu.objects.get(site=site, handle=handle)
        except Menu.DoesNotExist as e:
            if settings.DEBUG:
                raise e
            else:
                return ''

        templates_list: list[str] = []
        if template_name:
            templates_list.append(f'commontail/menu/menu.{template_name}.html')
        templates_list.extend([
            f'commontail/menu/menu.{handle}.html',
            'commontail/menu/menu.html'
        ])

        t: template.Template = select_template(templates_list)

        rendered_content: str = t.render({
            'menu': menu_obj,
            'template_name': template_name,
        })

        if template_name:
            Menu.set_cache_data(Menu.TEMPLATE_CACHE_PREFIX, rendered_content, (site, handle, template_name, ))
        else:
            Menu.set_cache_data(Menu.TEMPLATE_CACHE_PREFIX, rendered_content, (site, handle, ))

        return rendered_content


@register.tag
def build_menu(parser, token):
    tag_name: str
    handle: str
    template_name: Optional[str]
    try:
        tag_name, handle, template_name = token.split_contents()
    except ValueError:
        template_name = None
        try:
            tag_name, handle = token.split_contents()
        except ValueError:
            raise template.TemplateSyntaxError(
                f'{token.contents.split()[0]} tag takes one required argument - menu handle - and one optional - '
                f'template name.'
            )

    return MenuNode(handle, template_name)
