import os
import sys
from collections import defaultdict
from textwrap import dedent
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

import requests
import yaml

from openslides_backend.permissions.get_permission_parts import get_permission_parts

SOURCE = "https://raw.githubusercontent.com/OpenSlides/OpenSlides/openslides4-dev/docs/permission.yml"

DESTINATION = os.path.abspath(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "openslides_backend",
        "permissions",
        "permissions.py",
    )
)

FILE_TEMPLATE = dedent(
    """\
    # Code generated. DO NOT EDIT.

    from enum import Enum
    from typing import Dict, List

    from .get_permission_parts import get_permission_parts


    class OrganisationManagementLevel(str, Enum):
        SUPERADMIN = "superadmin"
        CAN_MANAGE_USERS = "can_manage_users"
        CAN_MANAGE_ORGANISATION = "can_manage_organisation"

        def __init__(self, oml: str):
            super().__init__()
            self.numbers = {
                "superadmin": 3,
                "can_manage_organisation": 2,
                "can_manage_users": 1,
            }
            self.number: int = self.numbers.get(oml, 0)

        def is_ok(self, user_oml: str) -> bool:
            return self.numbers.get(user_oml, 0) >= self.number


    class CommitteeManagementLevel(str, Enum):
        \""" 2nd Permission Type, implemented as User.committee_as_manager_ids \"""

        MANAGER = "can_manage_committees"

        def __init__(self, cml: str):
            super().__init__()
            self.numbers = {
                "can_manage_committees": 1,
            }
            self.number: int = self.numbers.get(cml, 0)

        def is_ok(self, user_cml: str) -> bool:
            return self.numbers.get(user_cml, 0) >= self.number


    class Permission(str):
        \""" Marker class to use typing with permissions. \"""

        def __str__(self) -> str:
                return self.value  # type: ignore
    """
)

PERMISSION_CLASS_TEMPLATE = dedent(
    """
    class Permissions:
        @classmethod
        def parse(cls, permission: str) -> Permission:
            parts = get_permission_parts(permission)
            PermissionClass = getattr(cls, parts[0])
            return getattr(PermissionClass, parts[1])
    """
)


class Permission(str):
    def __repr__(self) -> str:
        collection, permission = get_permission_parts(self)
        return f"_{collection}.{permission}"


def main() -> None:
    """
    Main entry point for this script to generate the permissions.py from permission.yml.
    """
    # Retrieve models.yml from call-parameter for testing purposes, local file or GitHub
    if len(sys.argv) > 1:
        file = sys.argv[1]
    else:
        file = SOURCE

    if os.path.isfile(file):
        with open(file, "rb") as x:
            permissions_yml = x.read()
    else:
        permissions_yml = requests.get(file).content

    # Load and parse permissions.yml
    permissions = yaml.safe_load(permissions_yml)
    with open(DESTINATION, "w") as dest:
        dest.write(FILE_TEMPLATE)
        all_parents: Dict[str, List[str]] = {}
        all_permissions: Dict[str, Set[str]] = defaultdict(set)
        for collection, children in permissions.items():
            parents = process_permission_level(collection, None, children)
            for pair in parents:
                collection, _ = get_permission_parts(pair[0])
                all_permissions[collection].add(pair[0])
                if not pair[0] in all_parents:
                    all_parents[pair[0]] = []
                if pair[1] is not None:
                    all_parents[pair[0]] += [pair[1]]

        for collection, permissions in all_permissions.items():
            dest.write(f"\nclass _{collection}(Permission, Enum):\n")
            for permission in permissions:
                _, perm_str = get_permission_parts(permission)
                dest.write(f"    {perm_str} = '{permission}'\n")

        dest.write(PERMISSION_CLASS_TEMPLATE)
        for collection in all_permissions.keys():
            dest.write(f"    {collection} = _{collection}\n")

        dest.write("\n# Holds the corresponding parent for each permission.\n")
        dest.write("permission_parents: Dict[Permission, List[Permission]] = ")
        dest.write(repr(all_parents))

    print(f"Permissions file {DESTINATION} successfully created.")


def process_permission_level(
    collection: str, permission: Optional[str], children: Dict[str, Any]
) -> Iterable[Tuple[str, Optional[str]]]:
    for child, grandchildren in children.items():
        if grandchildren:
            yield from process_permission_level(collection, child, grandchildren)
        parent = Permission(collection + "." + permission) if permission else None
        yield (Permission(collection + "." + child), parent)


if __name__ == "__main__":
    main()
