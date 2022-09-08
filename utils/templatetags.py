from typing import Optional, Type

from django import template
from django.conf import settings
from django.template.loader import select_template

from wagtail.models import Site

from ..models import AbstractCacheAware, AbstractSiteHandleModel


__all__ = ['HandleRenderedNode', ]


class HandleRenderedNode(template.Node):

    def __init__(self, model_class: Type[AbstractSiteHandleModel], template_prefix: str, handle: str,
                 template_name: Optional[str] = None, template_extension: Optional[str] = None):
        self.handle = template.Variable(handle)
        self.model_class: Type[AbstractSiteHandleModel] = model_class
        self.template_extension: Optional[str] = template_extension if template_extension else 'html'
        self.template_name = template.Variable(template_name) if template_name else None
        self.template_prefix: str = template_prefix

    def render(self, context):
        handle: str = self.handle.resolve(context)
        rendered_content: str
        template_name: Optional[str] = self.template_name.resolve(context) if self.template_name else None

        try:
            site: Site = Site.find_for_request(context['request'])
        except Site.DoesNotExist as e:
            if settings.DEBUG:
                raise e
            else:
                return ''

        if issubclass(self.model_class, AbstractCacheAware):
            extra: list[str] = [template_name] if template_name else []
            rendered_content = self.model_class.get_cache_provider().get_data(
                self.model_class.get_cache_template_prefix(), (site.pk, handle), extra
            )

            if rendered_content is not None:
                return rendered_content

        templates_list: list[str] = []
        if template_name:
            templates_list.append(f'{self.template_prefix}.{template_name}.{self.template_extension}')

        templates_list.extend([
            f'{self.template_prefix}.{handle}.{self.template_extension}',
            f'{self.template_prefix}.{self.template_extension}',
        ])
        t: template.Template = select_template(templates_list)

        try:
            instance: AbstractSiteHandleModel = self.model_class.objects.get(site=site, handle=handle)
        except self.model_class.DoesNotExist as e:
            if settings.DEBUG:
                raise e
            else:
                return ''

        rendered_content = t.render({
            'instance': instance,
            'template_name': template_name,
        })

        if issubclass(self.model_class, AbstractCacheAware):
            extra: list[str] = [template_name] if template_name else []
            self.model_class.get_cache_provider().set_data(
                self.model_class.get_cache_template_prefix(), rendered_content, (site.pk, handle), extra
            )

        return rendered_content
