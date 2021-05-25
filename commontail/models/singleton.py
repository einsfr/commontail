from django.http import HttpRequest

from wagtail.core.models import Page, Site


__all__ = ['PerSiteSingletonPage', ]


class PerSiteSingletonPage(Page):
    """
    Allows only one descendant page of this type per site.
    """

    class Meta:
        abstract = True

    @classmethod
    def can_create_at(cls, parent):
        site: Site = parent.get_site()

        return super().can_create_at(parent) and (
            site is not None and not parent.get_site().root_page.get_descendants().type(cls).exists()
        )

    @classmethod
    def get_for_site(cls, site: Site) -> Page:
        """
        Returns an instance of page with class 'cls' for site

        :param site: parent site for page instance
        :return: page instance
        """
        return site.root_page.get_descendants().type(cls).order('pk').first()

    @classmethod
    def get_for_request(cls, request: HttpRequest) -> Page:
        """
        Returns an instance of page with class 'cls' for request

        :param request: request instance
        :return: page instance
        """
        return cls.get_for_site(Site.find_for_request(request))
