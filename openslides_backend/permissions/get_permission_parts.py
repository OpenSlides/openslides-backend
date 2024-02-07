import re


def get_permission_parts(permission: str) -> tuple[str, str]:
    parts = permission.split(".")
    collection = parts[0].capitalize()
    collection = re.sub("_(.)", lambda pat: pat.group(1).upper(), collection)
    return (collection, parts[1].upper())
