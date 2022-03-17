from typing import Optional, Dict, Any, Set, Tuple, List

from django.http import HttpRequest
from django.conf import settings
from django.utils.functional import cached_property

from wagtail.core.models import Page


__all__ = ['AbstractSEOAwarePage', ]


class AbstractSEOAwarePage(Page):

    class Meta:
        abstract = True

    SEO_SITEMAP_SETTINGS_TEMPLATE: str = 'COMMONTAIL_SITEMAP_{}'
    SEO_SITEMAP_CHANGEFREQ_VALUES: Set[str] = {'always', 'hourly', 'daily', 'weekly', 'monthly', 'yearly', 'never'}

    seo_sitemap_settings_id: Optional[str] = None

    @cached_property
    def seo_title(self) -> str:
        return self._get_seo_title()

    @cached_property
    def seo_auto_meta_description(self) -> str:
        return self._get_seo_auto_meta_description()

    def _get_seo_auto_meta_description(self) -> str:
        return ''

    def _get_seo_title(self) -> str:
        return self.title

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context['allow_robots_indexing'] = self.get_seo_allow_indexing()
        context['canonical_url'] = self.get_seo_canonical_url(request)

        return context

    def get_seo_allow_indexing(self) -> bool:
        return settings.COMMONTAIL_SITEMAP_DEFAULT_ALLOW_INDEXING

    def get_seo_canonical_url(self, request: Optional[HttpRequest] = None) -> str:
        return self.get_full_url(request)

    def get_seo_include_in_sitemap(self) -> bool:
        return settings.COMMONTAIL_SITEMAP_DEFAULT_INCLUDE

    def get_seo_sitemap_addons(self) -> List[Dict]:
        return []

    def get_seo_sitemap_settings_id(self) -> Optional[str]:
        return self.seo_sitemap_settings_id

    def get_seo_changefreq_priority(self, settings_id: Optional[str]) -> Tuple[str, float]:
        changefreq: str
        priority: float
        try:
            changefreq, priority = getattr(
                settings, self.SEO_SITEMAP_SETTINGS_TEMPLATE.format(settings_id)
            )
        except TypeError:
            raise ValueError(f'Sitemap changefreq and priority settings must be in a tuple(changefreq, priority) '
                             f'format.')
        except AttributeError:
            return settings.COMMONTAIL_SITEMAP_DEFAULTS

        if str(changefreq) not in self.SEO_SITEMAP_CHANGEFREQ_VALUES:
            raise ValueError(f'Unknown sitemap changefreq value "{changefreq}" - see '
                             f'https://www.sitemaps.org/ru/protocol.html for more details.')
        try:
            if not (0.0 <= float(priority) <= 1.0):
                raise ValueError(f'Wrong sitemap priority value - float between 0.0 and 1.0 expected,'
                                 f'"{priority}" given.')
        except ValueError:
            raise ValueError(f'Wrong sitemap priority type - float expected, "{type(priority)}" given.')

    def get_sitemap_urls(self, request=None):
        settings_id: Optional[str] = self.get_seo_sitemap_settings_id()

        return [
            self.seo_update_sitemap_url(
                url, *self.get_seo_changefreq_priority(settings_id)
            ) for url in super().get_sitemap_urls()
            if self.get_seo_allow_indexing() and self.get_seo_include_in_sitemap()
        ] + self.get_seo_sitemap_addons()

    @staticmethod
    def seo_update_sitemap_url(url_dict: Dict[str, Any], changefreq: str, priority: float) -> Dict[str, Any]:
        url_dict.update({
            'changefreq': changefreq,
            'priority': priority,
        })

        return url_dict
