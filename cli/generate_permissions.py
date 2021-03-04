import os
import sys
from textwrap import dedent
from typing import Any, Dict, Iterable, Optional, Tuple

import requests
import yaml

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

    # Holds the corresponding parent for each permission.
    """
)


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
        all_parents = {}
        for collection, children in permissions.items():
            parents = process_permission_level(collection, None, children)
            for pair in parents:
                all_parents[pair[0]] = pair[1]
        dest.write("permissions = ")
        dest.write(repr(all_parents))

    print(f"Permissions file {DESTINATION} successfully created.")


def process_permission_level(
    collection: str, permission: Optional[str], children: Dict[str, Any]
) -> Iterable[Tuple[str, Optional[str]]]:
    for child, grandchildren in children.items():
        if grandchildren:
            yield from process_permission_level(collection, child, grandchildren)
        parent = collection + "." + permission if permission else None
        yield (collection + "." + child, parent)


if __name__ == "__main__":
    main()
