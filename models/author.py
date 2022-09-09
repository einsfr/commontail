from dataclasses import dataclass
from typing import Optional, Dict, Any, List, Type

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.forms.utils import ErrorList
from django.http import HttpRequest
from django.template.defaultfilters import truncatechars
from django.utils.translation import gettext_lazy as _

from wagtail.admin.panels import FieldPanel, MultiFieldPanel, PageChooserPanel
from wagtail.blocks import StructBlock, CharBlock, URLBlock, EmailBlock
from wagtail.fields import StreamField
from wagtail.models import Page, PageQuerySet, Site

from wagtailmodelchooser.blocks import ModelChooserBlock
from wagtailmodelchooser.edit_handlers import ModelChooserPanel

from .cache import AbstractCacheAwarePage, CacheMeta, CacheProvider
from .page import AbstractBaseIndexPage, AbstractContentStreamPage, AbstractImageAnnouncePage
from .singleton import AbstractPerSiteSingletonPage


__all__ = ['AbstractAuthorPage', 'AbstractAuthorsIndexPage', 'AbstractAuthorSignaturePage', 'FormattedSignatureData',
           'OtherAuthorBlock', 'Author', 'AuthorHomePageRelation', 'AuthorsPages']


AUTHOR_SIGNATURE_CACHE_PREFIX: str = 'author_signature'


class OtherAuthorBlock(StructBlock):

    class Meta:
        label = _('Not a user')
        icon = 'user'

    email = EmailBlock(label=_('e-mail'), required=False)

    text = CharBlock(max_length=64, label=_('Text'), required=True)

    url = URLBlock(label=_('URL'), required=False)

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


class AbstractAuthorPage(AbstractImageAnnouncePage, AbstractContentStreamPage):

    class Meta:
        abstract = True

    content_panels = Page.content_panels + AbstractImageAnnouncePage.content_panels + \
        AbstractContentStreamPage.content_panels

    def get_author(self) -> Optional['Author']:
        try:
            return AuthorHomePageRelation.objects.get(page=self)
        except AuthorHomePageRelation.DoesNotExist:
            return

    def get_author_pages(self) -> Optional[PageQuerySet]:
        author: 'Author' = self.get_author()

        if not author:
            return

        return author.get_pages()


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
        verbose_name = _('author')
        verbose_name_plural = _('authors')

    email = models.EmailField(
        blank=True,
        help_text=_("Author's public e-mail."),
        verbose_name=_('e-mail'),
    )

    first_name = models.CharField(
        help_text=_("Author's first name."),
        max_length=150,
        verbose_name=_('first name'),
    )

    last_name = models.CharField(
        help_text=_("Author's last name."),
        max_length=150,
        verbose_name=_('last name'),
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

    def get_pages(self, site: Site = None) -> PageQuerySet:
        author_pages: models.QuerySet = self.pages.get_queryset()
        if site:
            author_pages = author_pages.filter(site=site)

        return Page.objects.filter(pk__in=models.Subquery(author_pages.values('page_id')))


class AuthorHomePageRelation(models.Model):

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'site'], name='%(app_label)s_%(class)s_unique_author_site'
            )
        ]
        verbose_name = _('author home page')
        verbose_name_plural = _('authors home pages')

    author = models.ForeignKey(
        Author,
        on_delete=models.CASCADE,
        related_name='home_page',
        verbose_name=_('author'),
    )

    page = models.OneToOneField(
        Page,
        on_delete=models.CASCADE,
        related_name='+',
        verbose_name=_('page'),
    )

    site = models.ForeignKey(
        Site,
        editable=False,
        on_delete=models.CASCADE,
        related_name='+',
        verbose_name=_('site'),
    )

    panels = [
        ModelChooserPanel('author'),
        PageChooserPanel('page', page_type=settings.COMMONTAIL_AUTHOR_PAGE_MODEL or Page)
    ]

    def clean(self):
        self.site = self.page.get_site()

        super().clean()

    def validate_unique(self, exclude=None):  # wagtail will exclude site from unique checks because it's not editable
        if exclude:
            site_index: int = exclude.index('site')
            if site_index:
                del(exclude[site_index])

        super().validate_unique(exclude)


class AuthorsPages(models.Model):

    author = models.ForeignKey(
        Author,
        on_delete=models.CASCADE,
        related_name='pages',
        verbose_name=_('author')
    )

    page = models.ForeignKey(
        Page,
        on_delete=models.CASCADE,
        related_name='+',
        verbose_name=_('page'),
    )


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
            ('site_author', ModelChooserBlock(target_model=Author, label=_('Author'), icon='user')),
            ('other_author', OtherAuthorBlock()),
        ],
        blank=True,
        use_json_field=True,
        verbose_name=_('signature data'),
    )

    signature_original_url = models.URLField(
        blank=True,
        verbose_name=_('original publication URL'),
    )

    signature_use_owner = models.BooleanField(
        default=False,
        verbose_name=_('use page owner as an author'),
    )

    cache_prefixes = AbstractCacheAwarePage.cache_prefixes + {
        AUTHOR_SIGNATURE_CACHE_PREFIX: CacheMeta('default', settings.COMMONTAIL_AUTHOR_SIGNATURE_CACHE_LIFETIME)
    }

    promote_panels = [
        MultiFieldPanel(
            (
                FieldPanel('signature_use_owner'),
                FieldPanel('signature_original_url'),
                FieldPanel('signature_data'),
            ),
            heading=_('Author'),
        )
    ]

    def _signature_format_other_author(self, value: dict) -> FormattedSignatureData:
        return FormattedSignatureData(
            '', value['text'],
            value['url'] if value['url'] else f'mailto:{value["email"] if value["email"] else ""}', None
        )

    def _signature_format_site_author(self, author: Author) -> FormattedSignatureData:
        return FormattedSignatureData(
            '', author.get_full_name(), f'mailto:{author.email}' if author.email else '',
            {'title': author.email if author.email else ''}
        )

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
                return self._signature_format_site_author(author)
            else:
                if home_page.live:
                    return FormattedSignatureData(
                        '', author.get_full_name(), home_page.url,
                        {'title': _("Proceed to author's home page")}
                    )
                else:
                    return self._signature_format_site_author(author)

    def get_signature_data(self, request: HttpRequest) -> List[FormattedSignatureData]:
        cache_provider: CacheProvider = self.get_cache_provider()

        result: List[FormattedSignatureData] = cache_provider.get_data(
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

        cache_provider.set_data(AUTHOR_SIGNATURE_CACHE_PREFIX, result, self.get_cache_vary_on())

        return result

    def get_signature_first_author(self, request: HttpRequest) -> Optional[FormattedSignatureData]:
        try:
            return self.get_signature_data(request)[0]
        except IndexError:
            return

    @transaction.atomic
    def save(self, *args, **kwargs):
        # Published page is saved twice: first - draft is saved, second - draft is published...
        update_authors_pages: bool = False

        if 'update_fields' in kwargs:  # ... but only once with update_fields in kwargs
            if self.pk:
                old = self.__class__.objects.get(pk=self.pk)
                if old.signature_data != self.signature_data or old.signature_use_owner != self.signature_use_owner:
                    update_authors_pages = True
            else:
                update_authors_pages = True

        result = super().save(*args, **kwargs)

        # There is no matter if page is live or not, public or private - AuthorsPagesModel updates in all cases
        if update_authors_pages:
            AuthorsPages.objects.filter(page=self).delete()

            authors_list: list = []
            authors_pks: set = set()

            if self.signature_use_owner:
                try:
                    author: Author = Author.objects.get(user=self.owner)
                except Author.DoesNotExist:
                    pass
                else:
                    authors_list.append(author)
                    authors_pks.add(author.pk)

            for data in self.signature_data:
                if data.block_type == 'site_author' and data.value.pk not in authors_pks:
                    authors_list.append(data.value)
                    authors_pks.add(data.value.pk)

            AuthorsPages.objects.bulk_create(
                [AuthorsPages(author=author, page=self) for author in authors_list]
            )

        return result
