from typing import Any

from ..typing import Model

META_FIELD_PREFIX = "meta"
KEYSEPARATOR = "/"
META_DELETED = f"{META_FIELD_PREFIX}_deleted"
META_POSITION = f"{META_FIELD_PREFIX}_position"


def is_reserved_field(field: Any) -> bool:
    return isinstance(field, str) and field.startswith(META_FIELD_PREFIX)


def strip_reserved_fields(dictionary: Model) -> None:
    for k in list(dictionary.keys()):
        if is_reserved_field(k):
            del dictionary[k]
