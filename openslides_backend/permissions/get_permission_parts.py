import re
from typing import Tuple


def get_permission_parts(permission: str) -> Tuple[str, str]:
    parts = permission.split(".")
    collection = parts[0].capitalize()
    collection = re.sub("_(.)", lambda pat: pat.group(1).upper(), collection)
    return (collection, parts[1].upper())
