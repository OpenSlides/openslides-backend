import hashlib
import os
import sys
from collections import defaultdict
from collections.abc import Iterable
from textwrap import dedent
from typing import Any

import requests
import yaml

from openslides_backend.permissions.get_permission_parts import get_permission_parts

SOURCE = "./global/meta/permission.yml"

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

    from .base_classes import Permission

    PERMISSION_YML_CHECKSUM = "{}"
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
    if len(sys.argv) > 1 and sys.argv[1] != "check":
        file = sys.argv[1]
    else:
        file = SOURCE

    if os.path.isfile(file):
        with open(file, "rb") as x:
            permissions_yml = x.read()
    else:
        permissions_yml = requests.get(file).content

    # calc checksum to assert the permissions.py is up-to-date
    checksum = hashlib.md5(permissions_yml).hexdigest()

    if len(sys.argv) > 1 and sys.argv[1] == "check":
        from openslides_backend.permissions.permissions import PERMISSION_YML_CHECKSUM

        assert checksum == PERMISSION_YML_CHECKSUM
        print("permissions.py is up to date (checksum-comparison)")
        sys.exit(0)

    # Load and parse permissions.yml
    permissions = yaml.safe_load(permissions_yml)
    with open(DESTINATION, "w") as dest:
        dest.write(FILE_TEMPLATE.format(checksum))
        all_parents: dict[str, list[str]] = {}
        all_permissions: dict[str, set[str]] = defaultdict(set)
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
            dest.write(f"\nclass _{collection}(str, Permission, Enum):\n")
            for permission in sorted(permissions):
                _, perm_str = get_permission_parts(permission)
                dest.write(f"    {perm_str} = '{permission}'\n")

        dest.write("class Permissions:\n")
        for collection in all_permissions.keys():
            dest.write(f"    {collection} = _{collection}\n")

        dest.write("\n# Holds the corresponding parent for each permission.\n")
        dest.write("permission_parents: Dict[Permission, List[Permission]] = ")
        dest.write(repr(all_parents))

    print(f"Permissions file {DESTINATION} successfully created.")


def process_permission_level(
    collection: str, permission: str | None, children: dict[str, Any]
) -> Iterable[tuple[str, str | None]]:
    for child, grandchildren in children.items():
        if grandchildren:
            yield from process_permission_level(collection, child, grandchildren)
        parent = Permission(collection + "." + permission) if permission else None
        yield (Permission(collection + "." + child), parent)


if __name__ == "__main__":
    main()
