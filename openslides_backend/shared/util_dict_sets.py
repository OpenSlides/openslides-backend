from functools import reduce
from typing import Any, Dict, Iterable, List, Set


def get_set_from_dict_by_fieldlist(
    instance: Dict[str, Iterable[Any]], fieldlist: Iterable[str]
) -> Set[Any]:
    """
    Format of template field within read instance
    Function gets all fields of fieldlist from instance-dict,
    assuming they are all Iterables and reduces them to one set
    """
    return reduce(
        lambda i1, i2: i1 | i2,
        [set(instance.get(field, set())) or set() for field in fieldlist],
    )


def get_set_from_dict_from_dict(
    instance: Dict[str, Dict[str, List]], field: str
) -> Set[Any]:
    """
    Format of template field within payload
    Function gets field from instance-dict, which is a dict again.
    The values of these dicts have to be joined in a set.
    """
    cml = instance.get(field)
    if cml:
        return reduce(lambda i1, i2: i1 | i2, [set(values) for values in cml.values()])
    else:
        return set()
