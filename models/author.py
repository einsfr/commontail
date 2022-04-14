from dataclasses import dataclass
from typing import Optional, Dict, Any, List, Type

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.forms.utils import ErrorList
from django.http import HttpRequest
from django.template.defaultfilters import truncatechars
from django.utils.translation import gettext as _, gettext_lazy as _lazy

from wagtail.admin.edit_handlers import FieldPanel, StreamFieldPanel, MultiFieldPanel, PageChooserPanel
from wagtail.core.blocks import StructBlock, CharBlock, URLBlock, EmailBlock
from wagtail.core.fields import StreamField
from wagtail.core.models import Page, Site

from wagtailmodelchooser.blocks import ModelChooserBlock
from wagtailmodelchooser.edit_handlers import ModelChooserPanel

from .cache import AbstractCacheAwarePage, CacheMeta
from .page import AbstractBaseIndexPage, AbstractBasePage
from .singleton import AbstractPerSiteSingletonPage


__all__ = ['AbstractAuthorPage', 'AbstractAuthorsIndexPage', 'AbstractAuthorSignaturePage', 'FormattedSignatureData',
           'OtherAuthorBlock', 'Author', 'AuthorHomePageRelation', ]


AUTHOR_SIGNATURE_CACHE_PREFIX: str = 'author_signature'


class OtherAuthorBlock(StructBlock):

    class Meta:
        label = _lazy('Not a user')
        icon = 'user'

    email = EmailBlock(label=_lazy('e-mail'), required=False)

    text = CharBlock(max_length=64, label=_lazy('Text'), required=True)

    url = URLBlock(label=_lazy('URL'), required=False)

    def clean(self, value):
        result = super().clean(value)
        errors: dict = {}

        if value['url'] and value['email']:
            msg: str = _('URL or e-mail may be used - but not both of them at once.')
            errors['url'] = ErrorList([msg, ])
            errors['email'] = ErrorList([msg, ])

        if errors:
            raise ValidationError('Validation error in StructBlock', params=errors)

        return result


class AbstractAuthorPage(AbstractBasePage):

    class Meta:
        abstract = True


class AbstractAuthorsIndexPage(AbstractPerSiteSingletonPage, AbstractBaseIndexPage):

    class Meta:
        abstract = True

    def get_items_class(self) -> Type[Page]:
        raise NotImplementedError

    def get_items_queryset_filters(self, request) -> Optional[Dict]:
        raise NotImplementedError

    def get_per_page_number(self, request) -> int:
        raise NotImplementedError


class Author(models.Model):

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['first_name', 'last_name', 'email'],
                                    name='%(app_label)s_%(class)s_unique_author')
        ]
        verbose_name = _lazy('author')
        verbose_name_plural = _lazy('authors')

    email = models.EmailField(
        blank=True,
        help_text=_lazy("Author's public email."),
        verbose_name=_lazy('email'),
    )

    first_name = models.CharField(
        help_text=_lazy("Author's first name."),
        max_length=150,
        verbose_name=_lazy('first name'),
    )

    last_name = models.CharField(
        help_text=_lazy("Author's last name."),
        max_length=150,
        verbose_name=_lazy('last name'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )

    panels = [
        FieldPanel('first_name'),
        FieldPanel('last_name'),
        FieldPanel('email'),
        ModelChooserPanel('user'),
    ]

    def __str__(self):
        if self.email:
            return f'{self.get_full_name()} <{self.email}>'
        else:
            return self.get_full_name()

    def get_full_name(self) -> str:
        return f'{self.first_name} {self.last_name}'


class AuthorHomePageRelation(models.Model):

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'site', 'page'], name='%(app_label)s_%(class)s_unique_author_site_page'
            )
        ]
        verbose_name = _lazy('author home page')
        verbose_name_plural = _lazy('authors home pages')

    author = models.ForeignKey(
        Author,
        on_delete=models.CASCADE,
        related_name='home_page',
    )

    page = models.ForeignKey(
        Page,
        on_delete=models.CASCADE,
        related_name='+',
    )

    site = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
        related_name='+',
    )

    panels = [
        ModelChooserPanel('author'),
        FieldPanel('site'),
        PageChooserPanel('page', page_type=settings.COMMONTAIL_AUTHOR_PAGE_MODEL or Page)
    ]


@dataclass
class FormattedSignatureData:
    prefix: str
    title: str
    url: str
    attrs: Optional[Dict[str, Any]]


class AbstractAuthorSignaturePage(AbstractCacheAwarePage):

    class Meta:
        abstract = True

    signature_data = StreamField(
        [
            ('site_author', ModelChooserBlock(target_model=Author, label=_lazy('Author'), icon='user')),
            ('other_author', OtherAuthorBlock()),
        ],
        blank=True,
        verbose_name=_lazy('signature data'),
    )

    signature_original_url = models.URLField(
        blank=True,
        verbose_name=_lazy('original publication URL'),
    )

    signature_use_owner = models.BooleanField(
        default=True,
        verbose_name=_lazy('use page owner as an author'),
    )

    cache_prefixes = AbstractCacheAwarePage.cache_prefixes + {
        AUTHOR_SIGNATURE_CACHE_PREFIX: CacheMeta('default', settings.COMMONTAIL_AUTHOR_SIGNATURE_CACHE_LIFETIME)
    }

    promote_panels = [
        MultiFieldPanel(
            (
                FieldPanel('signature_use_owner'),
                FieldPanel('signature_original_url'),
                StreamFieldPanel('signature_data'),
            ),
            heading=_lazy('Author'),
        )
    ]

    def _signature_format_other_author(self, value: dict) -> FormattedSignatureData:
        return FormattedSignatureData(
            '', value['text'],
            value['url'] if value['url'] else f'mailto:{value["email"] if value["email"] else ""}', None
        )

    def _signature_format_site_author(self, author: Author) -> FormattedSignatureData:
        return FormattedSignatureData('', author.get_full_name(), author.email, None)

    def _signature_format_user(self, user: User, site: Site) -> FormattedSignatureData:
        try:
            author: Author = Author.objects.get(user=user)
        except Author.DoesNotExist:
            return FormattedSignatureData(
                '', user.get_full_name() or user.username, f'mailto:{user.email}' if user.email else '', None
            )
        else:
            try:
                home_page: Page = AuthorHomePageRelation.objects.select_related('page').get(
                    author=author, site=site).page
            except AuthorHomePageRelation.DoesNotExist:
                return FormattedSignatureData(
                    '', author.get_full_name(), f'mailto:{author.email}' if author.email else '',
                    {'title': author.email if author.email else ''}
                )
            else:
                return FormattedSignatureData(
                    '', author.get_full_name(), home_page.url,
                    {'title': _lazy("Proceed to author's home page")}
                )

    def get_signature_data(self, request: HttpRequest) -> List[FormattedSignatureData]:
        result: List[FormattedSignatureData] = self.get_cache_data(
            AUTHOR_SIGNATURE_CACHE_PREFIX, self.get_cache_vary_on())

        if result is not None:
            return result
        else:
            result = []

        site: Site = Site.find_for_request(request)

        if self.signature_use_owner and self.owner:
            result.append(self._signature_format_user(self.owner, site))

        for data in self.signature_data:
            if data.block_type == 'site_author':
                result.append(self._signature_format_site_author(data.value))
            elif data.block_type == 'other_author':
                result.append(self._signature_format_other_author(data.value))

        if self.signature_original_url:
            result.append(FormattedSignatureData(
                f'{_("source")}: ', truncatechars(self.signature_original_url, 64), self.signature_original_url,
                {'target': '_blank'}
            ))

        self.set_cache_data(AUTHOR_SIGNATURE_CACHE_PREFIX, result, self.get_cache_vary_on())

        return result

    def get_signature_first_author(self, request: HttpRequest) -> Optional[FormattedSignatureData]:
        try:
            return self.get_signature_data(request)[0]
        except IndexError:
            return
