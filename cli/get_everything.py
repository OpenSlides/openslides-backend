import logging
import os
import sys
from json import dumps

import openslides_backend.models.models  # noqa
from openslides_backend.services.database.extended_database import ExtendedDatabase
from openslides_backend.services.postgresql.db_connection_handling import (
    get_new_os_conn,
)
from openslides_backend.shared.env import Environment


def main() -> int:
    env = Environment(os.environ)

    with get_new_os_conn() as conn:
        database = ExtendedDatabase(conn, logging, env)

        everything = database.get_everything()
        print(dumps(everything, indent=4, sort_keys=True, default=str))

    return 0


if __name__ == "__main__":
    sys.exit(main())
