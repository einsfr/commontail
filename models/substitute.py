from typing import Iterable, Optional

from wagtail.models import Site


__all__ = ['SubstitutePage', ]


class SubstitutePage:

    def __init__(self, site: Site, title: str, url_path: str, ancestors: Iterable, seo_title: Optional[str] = None,
                 search_description: Optional[str] = None, **kwargs):
        self.site: Site = site
        self.title: str = title
        self.url_path: str = url_path
        self.ancestors: Iterable = ancestors
        self.seo_title: Optional[str] = seo_title
        self.search_description: Optional[str] = search_description

        self.is_substitute: bool = True

        self._kwargs: dict = kwargs

    def __getattr__(self, item):
        return self._kwargs.get('item', None)

    @property
    def full_url(self) -> str:
        return self.site.root_url + self.url_path

    def get_ancestors(self, inclusive: bool = False) -> Iterable:
        if not inclusive:
            return self.ancestors
        else:
            for a in self.ancestors:
                yield a

            yield self

    def get_site(self) -> Site:
        return self.site

    def is_root(self) -> bool:
        return False
