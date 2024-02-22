import argparse
import hashlib
from io import TextIOBase
import os
import sys
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path
from textwrap import dedent
from typing import Any

import requests
import yaml
from cli.util.util import assert_equal, open_output, open_yml_file, parse_arguments

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

    from .base_classes import Permission
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
    args = parse_arguments(SOURCE)
    permissions = open_yml_file(args.filename)
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

    with open_output(DESTINATION, args.check) as dest:
        dest.write(FILE_TEMPLATE)
        for collection, permissions in all_permissions.items():
            dest.write(f"\nclass _{collection}(str, Permission, Enum):\n")
            for permission in sorted(permissions):
                _, perm_str = get_permission_parts(permission)
                dest.write(f"    {perm_str} = '{permission}'\n")

        dest.write("class Permissions:\n")
        for collection in all_permissions.keys():
            dest.write(f"    {collection} = _{collection}\n")

        dest.write("\n# Holds the corresponding parent for each permission.\n")
        dest.write("permission_parents: dict[Permission, list[Permission]] = ")
        dest.write(repr(all_parents))

        if args.check:
            assert_equal(dest, DESTINATION)
            print("Permissions file up-to-date.")

            # check group.permissions enum in models.yml, if possible
            models_file = Path(args.filename).parent / "models.yml"
            if os.path.isfile(models_file):
                with open(models_file, "rb") as f:
                    models = yaml.safe_load(f.read())
                enum = set(models["group"]["permissions"]["items"]["enum"])
                permissions = {
                    str(permission)
                    for permissions in all_permissions.values()
                    for permission in permissions
                }
                assert enum == permissions, (
                    "Missing permissions: "
                    + str(permissions - enum)
                    + "\nAdditional permissions: "
                    + str(enum - permissions)
                )
                print("models.yml field group/permissions enum contains all permissions")
        else:
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
