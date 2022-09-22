from typing import Type, Optional, Union, List, Tuple


__all__ = ['collect_attributes', ]


def collect_attributes(cls: Union[Type, Tuple[Type]], attr_name: Union[str, List[str]],
                       break_class: Optional[Type] = None, reverse: bool = True,
                       as_dict: bool = True) -> Union[list, List[list], dict]:
    if isinstance(cls, tuple):
        cls = type('MROResolveHelper', cls, dict())

    result = []

    if type(attr_name) == str:
        attr_name = [str, ]

    for an in attr_name:
        result.append([])

    c: Type
    for c in cls.__mro__:
        for i, an in enumerate(attr_name):
            if an in c.__dict__:
                if reverse:
                    result[i] = getattr(c, an) + result[i]
                else:
                    result[i].extend(getattr(c, an))

        if c is break_class:
            break

    if as_dict:
        return dict(zip(attr_name, result))

    if len(attr_name) == 1:
        return result[0]
    else:
        return result
