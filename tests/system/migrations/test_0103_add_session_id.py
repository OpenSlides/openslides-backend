# BUILTIN IMPORTS
import os
from datetime import datetime, timedelta
from importlib import import_module
from time import sleep
from typing import Any

from openslides_backend.http.views import ActionView
from openslides_backend.migrations.migration_helper import MigrationState
from openslides_backend.services.postgresql.db_connection_handling import os_conn_pool
from tests.system.migrations.base_migration_test import BaseMigrationTestCase
from tests.system.util import get_route_path

migration_module = import_module(
    "openslides_backend.migrations.migrations.0100_init_reldb"
)

# VARIABLE DECLARATION
EXAMPLE_DATA_PATH = os.path.realpath(
    os.path.join(
        os.getcwd(), "tests", "system", "migrations", "legacy-example-data.json"
    )
)
DEPR_SQL_PATH = os.path.realpath(
    os.path.join(os.getcwd(), "tests", "system", "migrations", "deprecated_schema.sql")
)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin"
MIGRATIONS_URL = get_route_path(ActionView.migrations_route)
created_fqids: set()
data: dict[str, any] = {}


class TestMigration103(BaseMigrationTestCase):
    def test_table_exists(self) -> None:
        def assert_content_not_none(
            query: str, value: dict[str:Any] | None = None, error_message: str = ""
        ) -> None:
            """
            Checks whether the first element of the result for `query` matches `value`.
            `value` should be None if the expected result is just not None.
            Because of this behavior, it can't be compared to an expected result of None.
            """
            result = cur.execute(query).fetchone()
            if error_message:
                assert result, error_message
            else:
                assert (
                    result
                ), f"Database did not contain a result for this query.\n{query}"
            if value is not None:
                assert result == value

        response = self.request("finalize")
        assert response.json == {
            "success": True,
            "status": MigrationState.MIGRATION_RUNNING,
            "output": self.EXPECTED_INTRODUCTION
            + "For setting organization and meeting time zones using 'Europe/Berlin'.\nmigration started\n",
        }

        # Wait for migrate with a sec delay per iteration. TODO centralize this
        max_time = timedelta(seconds=self.MAX_WAIT)
        start = datetime.now()
        while (response := self.request("migrate").json) != {
            "success": True,
            "status": MigrationState.FINALIZED,
            "output": "",
        }:
            sleep(0.1)
            if datetime.now() - start > max_time:
                raise Exception(
                    f"The migration doesn't finish in {max_time}. {response}"
                )
        assert response == {
            "success": True,
            "status": MigrationState.FINALIZED,
            "output": "",
        }

        self.assert_indices_state(MigrationState.FINALIZED)

        with os_conn_pool.connection() as conn:
            with conn.cursor() as cur:
                # 1.1) Session ID table exists
                assert_content_not_none(
                    "SELECT * FROM blocked_sessions;",
                    None,
                    "Session ID table exists.",
                )
