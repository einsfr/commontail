from .opengraph import OpenGraphGlobalLogoImagePageProvider
from .page import AbstractContentStreamPage
from .singleton import AbstractPerSiteSingletonPage


__all__ = ['AbstractAboutPage', ]


class AbstractAboutPage(AbstractPerSiteSingletonPage, AbstractContentStreamPage):

    class Meta:
        abstract = True

    opengraph_provider = OpenGraphGlobalLogoImagePageProvider()
