from dataclasses import dataclass
from typing import Optional, Dict, Any, List, Type

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.forms.utils import ErrorList
from django.http import HttpRequest
from django.template.defaultfilters import truncatechars
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from wagtail.admin.panels import FieldPanel, MultiFieldPanel, PageChooserPanel
from wagtail.blocks import StructBlock, CharBlock, URLBlock, EmailBlock
from wagtail.fields import StreamField
from wagtail.models import Page, PageQuerySet, Site

from wagtailmodelchooser.blocks import ModelChooserBlock
from wagtailmodelchooser.edit_handlers import ModelChooserPanel

from .cache import AbstractCacheAwarePage, CacheMeta, CacheProvider
from .page import AbstractBaseIndexPage, AbstractImageAnnouncePage, AbstractBasePage
from .singleton import AbstractPerSiteSingletonPage


__all__ = ['AbstractAuthorPage', 'AbstractAuthorsIndexPage', 'AbstractAuthorSignaturePage', 'FormattedSignatureData',
           'OtherAuthorBlock', 'Author', 'AuthorHomePageRelation', 'AuthorsPages', 'AuthorManager', ]


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


class AbstractAuthorPage(AbstractImageAnnouncePage, AbstractBasePage):

    class Meta:
        abstract = True

    content_panels = Page.content_panels + AbstractImageAnnouncePage.content_panels

    @cached_property
    def author(self) -> Optional['Author']:
        return self.get_author()

    def get_author(self) -> Optional['Author']:
        try:
            return AuthorHomePageRelation.objects.get(page=self).author
        except AuthorHomePageRelation.DoesNotExist:
            return

    def get_author_pages(self) -> Optional[PageQuerySet]:
        author: 'Author' = self.author

        if not author:
            return

        return author.get_pages(self.get_site())

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        context['author'] = self.author

        return context


class AbstractAuthorsIndexPage(AbstractPerSiteSingletonPage, AbstractBaseIndexPage):

    class Meta:
        abstract = True

    def get_items_class(self) -> Type[Page]:
        raise NotImplementedError

    def get_per_page_number(self, request) -> int:
        raise NotImplementedError


class AuthorManager(models.Manager):

    def exists_in_descendants(self, page: Page) -> models.QuerySet:
        return self.get_queryset().filter(
            models.Exists(AuthorsPages.objects.filter(
                author_id=models.OuterRef('pk'), page__path__startswith=page.path, page__depth__gte=page.depth
            ))
        )


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

    objects = AuthorManager()

    panels = [
        FieldPanel('first_name'),
        FieldPanel('last_name'),
        FieldPanel('email'),
        ModelChooserPanel('user'),
    ]

    def __str__(self):
        return self.get_full_name()

    def get_home_page(self, site: Site) -> Optional[Page]:
        try:
            return self.home_pages.get(site=site).page

        except AuthorHomePageRelation.DoesNotExist:
            return

    def get_full_name(self) -> str:
        return f'{self.first_name} {self.last_name}'

    def get_pages(self, site: Site = None) -> PageQuerySet:
        return Page.objects.filter(self.get_pages_q(site))

    def get_pages_q(self, site: Site = None) -> models.Q:
        subquery: models.Subquery
        if site:
            subquery = models.Subquery(self.pages.filter(site=site).values('page_id'))
        else:
            subquery = models.Subquery(self.pages.values('page_id'))

        return models.Q(pk__in=subquery)


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
        related_name='home_pages',
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

    site = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
        related_name='+',
        verbose_name=_('site'),
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

    @staticmethod
    def signature_format_other_author(value: dict) -> FormattedSignatureData:
        return FormattedSignatureData(
            '', value['text'],
            value['url'] if value['url'] else f'mailto:{value["email"] if value["email"] else ""}', None
        )

    @staticmethod
    def signature_format_site_author(author: Author, site: Site) -> FormattedSignatureData:
        home_page: Page = author.get_home_page(site)

        if home_page and home_page.live:
            return FormattedSignatureData(
                '', author.get_full_name(), home_page.relative_url(site), {'title': _("Proceed to author's home page")}
            )

        return FormattedSignatureData(
            '', author.get_full_name(), f'mailto:{author.email}' if author.email else '',
            {'title': author.email if author.email else ''}
        )

    def get_signature_data(self, request: HttpRequest) -> List[FormattedSignatureData]:
        cache_provider: CacheProvider = self.get_cache_provider()

        result: List[FormattedSignatureData] = cache_provider.get_data(
            AUTHOR_SIGNATURE_CACHE_PREFIX, self.get_cache_vary_on())
        author_pks: set[int] = set()

        if result is not None:
            return result
        else:
            result = []

        site: Site = Site.find_for_request(request)

        if self.signature_use_owner and self.owner:
            try:
                author: Author = Author.objects.get(user=self.owner)
            except Author.DoesNotExist:
                result.append(
                    FormattedSignatureData(
                        '', self.owner.get_full_name() or self.owner.username,
                        f'mailto:{self.owner.email}' if self.owner.email else '',
                        None
                    )
                )
            else:
                result.append(self.signature_format_site_author(author, site))
                author_pks.add(author.pk)

        for data in self.signature_data:
            if data.block_type == 'site_author' and data.value.pk not in author_pks:
                result.append(self.signature_format_site_author(data.value, site))
            elif data.block_type == 'other_author':
                result.append(self.signature_format_other_author(data.value))

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
        # Published page is saved twice (or even three times for new pages)...
        is_new: bool = False
        update_authors_pages: bool = False

        if self.id is None:
            is_new = True
            update_authors_pages = True

        if 'update_fields' in kwargs:  # ... but only once with update_fields in kwargs; for new pages pk is already set
            old = self.__class__.objects.get(pk=self.pk)
            if old.signature_data != self.signature_data or old.signature_use_owner != self.signature_use_owner:
                update_authors_pages = True

        result = super().save(*args, **kwargs)

        # There is no matter if page is live or not, public or private - AuthorsPagesModel updates in all cases
        if update_authors_pages:
            if not is_new:
                AuthorsPages.objects.filter(page=self).delete()

            authors_list: list = []
            authors_pks: set = set()

            if self.signature_use_owner and self.owner:
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
                [AuthorsPages(author=author, page=self, site=self.get_site()) for author in authors_list]
            )

        return result
