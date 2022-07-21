import re

from typing import Any, Optional, Callable, Union, Iterable, Type

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db import models
from django.http.request import HttpRequest
from django.forms import Form
from django.utils.translation import gettext as _

from psycopg2.extras import NumericRange

from wagtail.core.models import Page

from .models import AbstractPageImporterFormModel


__all__ = ['AbstractPageImporter', ]


class AbstractPageImporter:

    form_model: Optional[Type[AbstractPageImporterFormModel]] = None

    multispace_re = re.compile(' +')

    page_id_attr: str = 'id'

    title: Optional[str] = None

    url_suffix: Optional[str] = None

    def __init__(self, request: HttpRequest, form: Form):
        self.form: Form = form
        self.request: HttpRequest = request

    @classmethod
    def get_object_by_lookup(cls, model: models.Model,
                             lookup: Union[str, Iterable[Union[str, tuple[str, Callable]]]], value) -> models.Model:
        fk_value: models.Model

        if type(lookup) == str:
            fk_value = model.objects.get(**{lookup: value})
        else:
            lookup_dict: dict[str, Any]
            q: Optional[models.Q] = None

            for lk in lookup:
                if type(lk) == str:
                    lk: str
                    lookup_dict = {lk: value}
                else:
                    lk: tuple[str, Callable]
                    lookup_dict = {lk[0]: lk[1](value)}

                if q is None:
                    q = models.Q(**lookup_dict)
                else:
                    q = q | models.Q(**lookup_dict)

            fk_value = model.objects.get(q)

        return fk_value

    @classmethod
    def is_empty(cls, value: Any):
        return (value is None) or (type(value) == str and value == '')

    def process_form(self):
        raise NotImplementedError

    @classmethod
    def process_str_value(cls, value: str, **kwargs) -> str:
        if kwargs.get('lowercase', False):
            value = value.lower()

        if kwargs.get('uppercase', False):
            value = value.upper()

        if 'mapping' in kwargs:
            value = str(kwargs['mapping'].get(value, value))

        return value

    @classmethod
    def update_fk_value(cls, item: Page, item_id: Any, value: Any, attr_name: str,
                        simulation: bool, **kwargs) -> tuple[bool, list[str], list[str]]:
        if 'model' not in kwargs or 'lookup' not in kwargs:
            raise KeyError('Method update_fk_value requires "model" and "lookup" values in kwargs.')

        if value:
            value = cls.multispace_re.sub(' ', str(value)).strip()

            try:
                value = cls.get_object_by_lookup(kwargs['model'], kwargs['lookup'], value)
            except ObjectDoesNotExist:
                return False, [], [
                    _(
                        'Page <id:%(item_id)s> - there is no "%(model)s" instance for value "%(value)s" and '
                        'lookup expression "%(lookup)s".'
                    ) % {'item_id': item_id, 'model': kwargs['model'], 'value': value, 'lookup': kwargs['lookup']}
                ]
            except MultipleObjectsReturned:
                return False, [], [
                    _(
                        'Page <id:%(item_id)s> - there are multiple "%(model)s" instances for value "%(value)s" '
                        'and lookup expression "%(lookup)s".'
                    ) % {'item_id': item_id, 'model': kwargs['model'], 'value': value, 'lookup': kwargs['lookup']}
                ]
        else:
            value = None

        return cls.update_value(item, item_id, value, attr_name, simulation)

    @classmethod
    def update_float_range_value(cls, item: Page, item_id: Any, value: Any, attr_name: str,
                                 simulation: bool, **kwargs) -> tuple[bool, list[str], list[str]]:
        def _to_float(x: Any) -> float:
            return float(x.replace(',', '.')) if type(x) == str else float(x)

        try:
            lower, upper = map(lambda x: _to_float(x) if not cls.is_empty(x) else None, value)
        except ValueError:
            return False, [], [
                _(
                    'Page <id:%(item_id)s> - attribute "%(attr_name)s" range has at least one non-numeric value - '
                    'no updates will be made.'
                ) % {'item_id': item_id, 'attr_name': attr_name}
            ]

        return cls.update_value(
            item, item_id, NumericRange(lower, upper) if lower is not None or upper is not None else None,
            attr_name, simulation
        )

    @classmethod
    def update_float_value(cls, item: Page, item_id: Any, value: Any, attr_name: str,
                           simulation: bool, **kwargs) -> tuple[bool, list[str], list[str]]:
        if value:
            try:
                value = float(str(value).replace(',', '.'))
            except ValueError:
                return False, [], [
                    _(
                        'Page <id:%(item_id)s> - attribute "%(attr_name)s" is not a float - no updates will be made.'
                    ) % {'item_id': item_id, 'attr_name': attr_name}
                ]
        else:
            value = None

        return cls.update_value(item, item_id, value, attr_name, simulation)

    @classmethod
    def update_int_range_value(cls, item: Page, item_id: Any, value: Any, attr_name: str,
                               simulation: bool, **kwargs) -> tuple[bool, list[str], list[str]]:
        try:
            lower, upper = map(lambda x: int(x) if not cls.is_empty(x) else None, value)
        except ValueError:
            return False, [], [
                _(
                    'Page <id:%(item_id)s> - attribute "%(attr_name)s" range has at least one non-integer value - '
                    'no updates will be made.'
                ) % {'item_id': item_id, 'attr_name': attr_name}
            ]

        return cls.update_value(
            item, item_id, NumericRange(lower, upper) if lower is not None or upper is not None else None,
            attr_name, simulation
        )

    @classmethod
    def update_int_value(cls, item: Page, item_id: Any, value: Any, attr_name: str,
                         simulation: bool, **kwargs) -> tuple[bool, list[str], list[str]]:
        if value:
            try:
                value = int(value)
            except ValueError:
                return False, [], [
                    _(
                        'Page <id:%(item_id)s> - attribute "%(attr_name)s" is not an integer - no updates will be made.'
                    ) % {'item_id': item_id, 'attr_name': attr_name}
                ]
        else:
            value = None

        return cls.update_value(item, item_id, value, attr_name, simulation)

    @classmethod
    def update_m2m_value(cls, item: Page, item_id: Any, value: Any, attr_name: str,
                         simulation: bool, **kwargs) -> tuple[bool, list[str], list[str]]:
        if 'model' not in kwargs or 'lookup' not in kwargs:
            raise KeyError('Method update_fk_value requires "model" and "lookup" values in kwargs.')

        if not value:
            item_values = list(getattr(item, attr_name).all())

            if not item_values:
                return False, [], []

            if simulation:
                return True, [
                    _(
                        'Page <id:%(item_id)s> - relation "%(attr_name)s" changed from "%(data)s" to "[]".'
                    ) % {'item_id': item_id, 'attr_name': attr_name, 'data': [str(i) for i in item_values]}
                ], []

            getattr(item, attr_name).clear()

            return True, [], []

        values_set = set(map(lambda x: cls.multispace_re.sub(' ', str(x)).strip(), str(value).split(';')))

        try:
            m2m_values = list(map(lambda x: cls.get_object_by_lookup(kwargs['model'], kwargs['lookup'], x), values_set))
        except ObjectDoesNotExist:
            return False, [], [
                _(
                    'Page <id:%(item_id)s> - at least one instance of "%(model)s" for relation "%(attr_name)s" '
                    'is missing - no updates will be made.'
                ) % {'item_id': item_id, 'model': kwargs['model'], 'attr_name': attr_name}
            ]
        except MultipleObjectsReturned:
            return False, [], [
                _(
                    'Page <id:%(item_id)s> - at least once multiple "%(model)s" instances for relation "%(attr_name)s" '
                    'was found - no updates will be made.'
                ) % {'item_id': item_id, 'model': kwargs['model'], 'attr_name': attr_name}
            ]

        item_values = list(getattr(item, attr_name).all())

        if len(m2m_values) != len(item_values) or any(map(lambda x: x not in item_values, m2m_values)):
            if simulation:
                return True, [
                    _(
                        'Page <id:%(item_id)s> - relation "%(attr_name)s" changed from "%(old_value)s" to '
                        '"%(new_value)s".'
                    ) % {
                        'item_id': item_id, 'attr_name': attr_name, 'old_value': [str(i) for i in item_values],
                        'new_value': [str(i) for i in m2m_values]
                    }
                ], []

            getattr(item, attr_name).set(m2m_values)

            return True, [], []

        return False, [], []


    @classmethod
    def update_str_value(cls, item: Page, item_id: Any, value: Any, attr_name: str,
                         simulation: bool, **kwargs) -> tuple[bool, list[str], list[str]]:
        return cls.update_value(
            item, item_id, cls.process_str_value(
                cls.multispace_re.sub(' ', str(value)).strip() if value else '', **kwargs
            ),
            attr_name, simulation, getter=str, blank_value=''
        )

    @classmethod
    def update_value(cls, item: Page, item_id: Any, value: Any, attr_name: str, simulation: bool,
                     getter: Callable = None, blank_value: Any = None) -> tuple[bool, list[str], list[str]]:
        updated: bool = False
        errors: list[str] = []
        warnings: list[str] = []

        if item.pk:
            if value is None:
                value = blank_value

            item_value: Any = getter(getattr(item, attr_name)) if getter else getattr(item, attr_name)

            if item_value != value:
                if simulation:
                    warnings.append(_(
                        'Page <id:%(item_id)s> - attribute "%(attr_name)s" changed from "%(item_value)s" to '
                        '"%(value)s".'
                    ) % {'item_id': item_id, 'attr_name': attr_name, 'item_value': item_value, 'value': value})

                setattr(item, attr_name, value)
                updated = True

                if attr_name == 'title':
                    warnings.append(_(
                        'Page <id:%(item_id)s> - title changed, maybe you should change slug too '
                        'and create a redirect.'
                    ) % {'item_id': item_id})

                    if not item.live:
                        item.draft_title = value
                elif attr_name == 'slug':
                    warnings.append(_(
                        'Page <id:%(item_id)s> - slug changed, maybe you should create a redirect.'
                    ) % {'item_id': item_id})
        else:
            if value is None or value == blank_value:
                if simulation:
                    warnings.append(_(
                        'Page <id:%(item_id)s> - attribute "%(attr_name)s" not set - skipping...'
                    ) % {'item_id': item_id, 'attr_name': attr_name})
            else:
                setattr(item, attr_name, value)
                updated = True

                if attr_name == 'title':
                    item.draft_title = value

        return updated, warnings, errors
