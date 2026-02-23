import logging
import os
import sys

from openslides_backend.presenter.check_database import check_meetings
from openslides_backend.presenter.check_database_all import check_everything
from openslides_backend.services.database.extended_database import ExtendedDatabase
from openslides_backend.services.postgresql.db_connection_handling import (
    get_new_os_conn,
)
from openslides_backend.shared.env import Environment


def main() -> int:
    env = Environment(os.environ)

    arg = sys.argv[1] if len(sys.argv) > 1 else None
    with get_new_os_conn() as conn:
        datastore = ExtendedDatabase(conn, logging, env)
        if arg == "all":
            check_everything(datastore)
        else:
            meeting_id = int(arg) if arg else None
            errors = check_meetings(datastore, meeting_id)
            if errors:
                for meeting_id, error in errors.items():
                    print(f"Meeting {meeting_id}: {error}")
                return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
