from dataclasses import dataclass
from typing import Optional, Dict, Any, Iterable

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.forms.utils import ErrorList
from django.template.defaultfilters import truncatechars
from django.utils.translation import gettext as _, gettext_lazy as _lazy

from wagtail.admin.edit_handlers import FieldPanel, StreamFieldPanel, MultiFieldPanel
from wagtail.core.blocks import StructBlock, CharBlock, URLBlock, EmailBlock
from wagtail.core.fields import StreamField
from wagtail.core.models import Page

from wagtailmodelchooser.blocks import ModelChooserBlock


__all__ = ['AbstractAuthorSignaturePage', 'FormattedSignatureData', ]


class NotUserBlock(StructBlock):

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


@dataclass
class FormattedSignatureData:
    prefix: str
    title: str
    url: str
    attrs: Optional[Dict[str, Any]]


class AbstractAuthorSignaturePage(Page):

    class Meta:
        abstract = True

    signature_data = StreamField(
        [
            ('user', ModelChooserBlock(settings.AUTH_USER_MODEL, label=_lazy('user'), icon='user')),
            ('not_user', NotUserBlock()),
        ],
        blank=True,
        verbose_name=_lazy('signature data'),
    )

    signature_original_url = models.URLField(
        blank=True,
        verbose_name=_lazy('original publication URL'),
    )

    signature_use_owner = models.BooleanField(
        default=False,
        verbose_name=_lazy('use page owner as an author'),
    )

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

    @staticmethod
    def _signature_format_user(user: User) -> FormattedSignatureData:
        full_name: str = user.get_full_name()

        return FormattedSignatureData('', full_name if full_name else user.username, f'mailto:{user.email}', None)

    @staticmethod
    def _signature_format_not_user(value: dict) -> FormattedSignatureData:
        return FormattedSignatureData(
            '', value['text'],
            value['url'] if value['url'] else f'mailto:{value["email"] if value["email"] else ""}', None
        )

    def get_signature_data(self) -> Iterable[FormattedSignatureData]:

        if self.signature_use_owner and self.owner:
            yield self._signature_format_user(self.owner)

        for data in self.signature_data:
            if data.block_type == 'user':
                yield self._signature_format_user(data.value)
            elif data.block_type == 'not_user':
                yield self._signature_format_not_user(data.value)

        if self.signature_original_url:
            yield FormattedSignatureData(
                f'{_("source")}: ', truncatechars(self.signature_original_url, 64), self.signature_original_url,
                {'target': '_blank'}
            )

    def get_signature_first_author(self) -> Optional[FormattedSignatureData]:
        return next(iter(self.get_signature_data()), None)
