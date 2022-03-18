import abc

from collections.abc import Mapping
from typing import Optional, Dict, Any, List, Tuple, Callable, Set, Iterable

from django.conf import settings
from django.http import HttpRequest
from django.utils.translation import to_locale

from wagtail.images.models import AbstractImage, AbstractRendition

from .cache import AbstractCacheAwarePage, CacheMeta
from .settings import get_logo


__all__ = ['OPENGRAPH_ADDITIONAL_NAMESPACES', 'OPENGRAPH_BASE_TYPE', 'OPENGRAPH_CACHE_PREFIX',
           'OPENGRAPH_NAMESPACE_URLS', 'get_opengraph_image_data', 'get_namespace_from_type',
           'AbstractOpenGraphProvider', 'OpenGraphPageProvider',
           'OpenGraphGlobalLogoImagePageProvider', 'OpenGraphAware', 'AbstractOpenGraphAwarePage']


OPENGRAPH_ADDITIONAL_NAMESPACES: Set[str] = {'article', 'book', 'music', 'profile', 'video'}
OPENGRAPH_BASE_TYPE: str = 'website'
OPENGRAPH_CACHE_PREFIX: str = 'opengraph'
OPENGRAPH_NAMESPACE_URLS: Dict[str, str] = {
    'article': 'https://ogp.me/ns/article#',
    'book': 'https://ogp.me/ns/book#',
    'music': 'https://ogp.me/ns/music#',
    'og': 'https://ogp.me/ns#',
    'profile': 'https://ogp.me/ns/profile#',
    'video': 'https://ogp.me/ns/video#',
}


def get_opengraph_image_data(image: Optional[AbstractImage]) -> Optional[Dict[str, Any]]:
    """
    Prepares image metadata in opengraph-required format

    :param image: image instance
    :return: dict with image metadata
    """
    if not image:
        return

    rendition: AbstractRendition = image.get_rendition('original')

    return {
        '': rendition.url,
        'width': rendition.width,
        'height': rendition.height,
        'alt': rendition.alt,
    }


def get_namespace_from_type(opengraph_type: str) -> str:
    """
    Returns namespace part from types like 'video.movie'

    :param opengraph_type: opengraph type
    :return: namespace
    """
    return opengraph_type.split('.')[0]


class AbstractOpenGraphProvider(abc.ABC):
    """
    Abstract provider of opengraph data
    """

    attrs: List[str] = ['title', 'image', 'url', 'audio', 'description', 'determiner', 'locale', 'site_name', 'video']

    @abc.abstractmethod
    def get_og_title(self, data_object: 'OpenGraphAware', request: HttpRequest) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def get_og_image(self, data_object: 'OpenGraphAware', request: HttpRequest) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_og_url(self, data_object: 'OpenGraphAware', request: HttpRequest) -> str:
        raise NotImplementedError

    @classmethod
    def _process_value(cls, attr: Any, value: Any) -> List[Tuple[str, Any]]:
        if isinstance(value, Mapping):
            result: List[Tuple[str, Any]] = []
            for k, v in value.items():
                if attr not in OPENGRAPH_ADDITIONAL_NAMESPACES:
                    result.append((f'og:{attr}:{k}' if k else f'og:{attr}', v))
                else:
                    result.append((f'{attr}:{k}' if k else attr, v))

            return result

        if type(value) != str:
            try:
                _ = iter(value)
            except TypeError:
                pass
            else:
                return [i for v in value for i in cls._process_value(attr, v)]

        if attr not in OPENGRAPH_ADDITIONAL_NAMESPACES:
            return [(f'og:{attr}', value)]
        else:
            return [(str(attr), value)]

    def get_data(self, data_object: 'OpenGraphAware', request: HttpRequest) -> List[Tuple[str, Any]]:
        """
        Collects opengraph data from OpenGraphAware object

        All data is collected from get_* methods, where * means modified attribute name. For example: get_og_title or
        get_site_name.
        :param data_object:
        :param request:
        :return:
        """
        object_type: str = data_object.get_opengraph_type()
        result: List[Tuple[str, Any]] = [('og:type', object_type)]
        attrs: List[str] = [*self.attrs]  # copy self.attrs to prevent modification of class variable
        object_type_namespace: str = get_namespace_from_type(object_type)

        if object_type_namespace in OPENGRAPH_ADDITIONAL_NAMESPACES:
            attrs.append(object_type_namespace)

        a: str
        for a in attrs:
            callback: Callable[['OpenGraphAware', HttpRequest], Any] = getattr(
                self, f'get_og_{a.replace(":", "_")}', None)

            if not callback:
                continue

            value: Any = callback(data_object, request)

            if not value:
                continue

            result.extend(self._process_value(a, value))

        return result

    @staticmethod
    def get_namespaces(data_object: 'OpenGraphAware') -> List[Tuple[str, str]]:
        result: List[Tuple[str, str]] = [('og', OPENGRAPH_NAMESPACE_URLS.get('og'))]
        namespace: str = get_namespace_from_type(data_object.get_opengraph_type())
        if namespace in OPENGRAPH_ADDITIONAL_NAMESPACES:
            result.append((namespace, OPENGRAPH_NAMESPACE_URLS.get(namespace)))

        return result


class OpenGraphPageProvider(AbstractOpenGraphProvider):

    def __init__(self, image_attribute: Optional[str] = None, description_attribute: Optional[str] = None):
        self.image_attribute: Optional[str] = image_attribute
        self.description_attribute: Optional[str] = description_attribute

    @staticmethod
    def _get_image_data(data_object: 'AbstractOpenGraphAwarePage', image: Optional[AbstractImage]):
        image_data: Dict[str, Any] = get_opengraph_image_data(image)

        if not image_data:
            return

        image_data[''] = f"{data_object.get_site().root_url}{image_data['']}"  # convert relative URL to absolute

        return image_data

    def get_og_title(self, data_object: 'AbstractOpenGraphAwarePage', request: HttpRequest) -> str:
        return data_object.seo_title or data_object.title

    def get_og_image(self, data_object: 'AbstractOpenGraphAwarePage', request: HttpRequest) -> Optional[Dict[str, Any]]:
        if self.image_attribute:
            return self._get_image_data(data_object, getattr(data_object, self.image_attribute, None))
        else:
            return

    def get_og_url(self, data_object: 'AbstractOpenGraphAwarePage', request: HttpRequest) -> str:
        return data_object.full_url

    def get_og_description(self, data_object: 'AbstractOpenGraphAwarePage', request: HttpRequest) -> str:
        if self.description_attribute:
            return getattr(data_object, self.description_attribute, None)

        return data_object.search_description

    def get_og_locale(self, data_object: 'AbstractOpenGraphAwarePage', request: HttpRequest) -> str:
        # TODO: in multilingual sites this will not work correctly
        return to_locale(settings.LANGUAGE_CODE)

    def get_og_site_name(self, data_object: 'AbstractOpenGraphAwarePage', request: HttpRequest) -> str:
        return data_object.get_site().site_name

    def get_og_article(self, data_object: 'AbstractOpenGraphAwarePage', request: HttpRequest) -> Dict[str, Any]:
        result = dict()

        if data_object.go_live_at:
            result['published_time'] = data_object.go_live_at.strftime('%Y-%m-%d')
        elif data_object.first_published_at:
            result['published_time'] = data_object.first_published_at.strftime('%Y-%m-%d')

        if data_object.first_published_at != data_object.last_published_at:
            result['modified_time'] = data_object.last_published_at.strftime('%Y-%m-%d')

        return result


class OpenGraphGlobalLogoImagePageProvider(OpenGraphPageProvider):

    def get_og_image(self, data_object: 'AbstractOpenGraphAwarePage', request: HttpRequest) -> Optional[Dict[str, Any]]:
        logo: AbstractImage = get_logo(request=request, square=True)

        if not logo:
            return

        return self._get_image_data(data_object, logo)


class OpenGraphAware:

    opengraph_provider: Optional[AbstractOpenGraphProvider] = None
    opengraph_type: Optional[str] = None

    def get_opengraph_namespaces(self) -> List[Tuple[str, str]]:
        return self.opengraph_provider.get_namespaces(self)

    def get_opengraph_data(self, request: HttpRequest) -> List[Tuple[str, Any]]:
        return self.opengraph_provider.get_data(self, request)

    def get_opengraph_type(self) -> str:
        return self.opengraph_type if self.opengraph_type else OPENGRAPH_BASE_TYPE


class AbstractOpenGraphAwarePage(OpenGraphAware, AbstractCacheAwarePage):

    class Meta:
        abstract = True

    cache_prefixes = AbstractCacheAwarePage.cache_prefixes + {
        OPENGRAPH_CACHE_PREFIX: CacheMeta('default', settings.COMMONTAIL_OPENGRAPH_CACHE_LIFETIME)
    }

    opengraph_provider: Optional[AbstractOpenGraphProvider] = OpenGraphPageProvider()

    def get_cache_vary_on(self) -> Iterable[Any]:
        return self.pk,

    def get_opengraph_data(self, request: HttpRequest) -> List[Tuple[str, Any]]:
        data: List[Tuple[str, Any]] = self.get_cache_data(
            OPENGRAPH_CACHE_PREFIX, self.get_cache_vary_on())

        if data is None:
            data = super().get_opengraph_data(request)
            self.set_cache_data(OPENGRAPH_CACHE_PREFIX, data, self.get_cache_vary_on())

        return data
