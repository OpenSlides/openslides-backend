from typing import Optional

from .permissions import permissions


def is_child_permission(child: str, parent: str) -> bool:
    """
    Iterate the permission tree (represented in the permissions object) from child to
    parent or until there is no parent.
    """
    current: Optional[str] = child
    while current:
        if current == parent:
            return True
        current = permissions[current]
    return False
