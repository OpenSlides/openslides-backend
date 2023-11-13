import os
from io import StringIO

import pytest
from datastore.migrations.core.migration_handler import MigrationHandler
from datastore.shared.di import injector
from datastore.shared.postgresql_backend import ConnectionHandler

from openslides_backend.migrations.migrate import MigrationWrapper

SQL_FILE = "tests/dump.sql"


@pytest.mark.skipif(not os.path.isfile(SQL_FILE), reason="No SQL dump found")
def test_with_sql_dump():
    connection_handler = injector.get(ConnectionHandler)
    with connection_handler.get_connection_context():
        with connection_handler.get_current_connection().cursor() as cursor:
            with open(SQL_FILE, "r") as file:
                content = file.read()
                if content.startswith("COPY"):
                    cursor.execute("SET session_replication_role = 'replica'")
                    lines = content.split("\n")
                    while lines:
                        line = lines.pop(0).strip()
                        if line.startswith("--") or line == "":
                            continue
                        assert line.startswith("COPY")
                        data = StringIO()
                        while (record := lines.pop(0).strip()) != "\\.":
                            data.write(record + "\n")
                        data.seek(0)
                        cursor.copy_expert(line, data)
                    cursor.execute("SET session_replication_role = 'origin'")
                else:
                    cursor.execute(content, [])
    migration_handler = injector.get(MigrationHandler)
    migration_handler.register_migrations(
        *MigrationWrapper.load_migrations("openslides_backend.migrations.migrations")
    )
    migration_handler.finalize()
