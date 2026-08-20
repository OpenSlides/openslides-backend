# BUILTIN IMPORTS
import json
import os
from collections.abc import Callable
from datetime import datetime, timedelta
from importlib import import_module
from io import StringIO
from threading import Lock
from time import sleep
from typing import Any
from unittest.mock import DEFAULT as mockdefault
from unittest.mock import Mock, patch
from zoneinfo import ZoneInfo

from meta.dev.src.generate_sql_schema import GenerateCodeBlocks
from openslides_backend.http.application import OpenSlidesBackendWSGIApplication
from openslides_backend.http.views import ActionView
from openslides_backend.migrations.migration_handler import MigrationHandler
from openslides_backend.migrations.migration_helper import (
    MIN_NON_REL_MIGRATION,
    MigrationHelper,
    MigrationState,
)
from openslides_backend.migrations.migration_manager import MigrationManager
from openslides_backend.services.auth.interface import AuthenticationService
from openslides_backend.services.postgresql.create_schema import (
    create_db,
    create_schema,
    drop_db,
)
from openslides_backend.services.postgresql.db_connection_handling import (
    get_new_os_conn,
    get_unpooled_db_connection,
    os_conn_pool,
)
from openslides_backend.shared.env import DEV_PASSWORD
from tests.conftest import OLD_TABLES, get_rel_db_table_names
from tests.conftest_helper import (
    deactivate_notify_triggers,
    generate_sql_for_test_initiation,
)
from tests.system.action.util import get_internal_auth_header
from tests.system.migrations.base_migration_test import BaseMigrationTestCase
from tests.system.util import create_action_test_application, get_route_path
from tests.util import AuthData, Client, Response

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
                    "SELECT * FROM session_id;",
                    None,
                    "Session ID table exists.",
                )
