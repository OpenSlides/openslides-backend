import os
import re
from collections.abc import Callable
from datetime import datetime
from decimal import Decimal
from json import dumps as json_dumps
from threading import Lock
from typing import Any
from unittest import TestCase
from unittest import TestResult as UnitTestResult
from unittest.mock import DEFAULT as mockdefault
from unittest.mock import MagicMock, Mock, patch
from zoneinfo import ZoneInfo

from psycopg import Cursor
from psycopg.rows import DictRow

from openslides_backend.http.views import ActionView
from openslides_backend.migrations.migration_helper import (
    MIGRATIONS_PATH,
    MIN_NON_REL_MIGRATION,
    MigrationHelper,
)
from openslides_backend.migrations.migration_manager import MigrationManager
from openslides_backend.models.fields import (
    DecimalField,
    Field,
    JSONField,
    TimestampField,
)
from openslides_backend.services.database.extended_database import ExtendedDatabase
from openslides_backend.services.postgresql.create_schema import create_schema
from openslides_backend.services.postgresql.db_connection_handling import (
    get_new_os_conn,
)
from openslides_backend.services.postgresql.utils import deactivate_notify_triggers
from tests.conftest import get_rel_db_table_names
from tests.conftest_helper import generate_sql_for_test_initiation
from tests.system.util import get_route_path

DEPR_SQL_PATH = os.path.realpath(
    os.path.join(os.getcwd(), "tests", "system", "migrations", "deprecated_schema.sql")
)
MIGRATIONS_URL = get_route_path(ActionView.migrations_route)


class BaseMigrationTestCase(TestCase):
    # has to be set by subclass
    migration_number: int

    def run(self, result: UnitTestResult | None = None) -> UnitTestResult | None:
        """
        Overrides the TestCases run method.
        Provides an ExtendedDatabase in self.datastore with an open psycopg connection.
        Also stores its connection in self.connection.
        """
        with get_new_os_conn() as conn:
            self.datastore = ExtendedDatabase(conn, MagicMock(), MagicMock())
            self.connection = conn
            return super().run(result)

    def setUp(self) -> None:
        """
        Does not call super class to prevent usage of client and so forth.
        """
        os.environ["MIG0100_TIMEZONE"] = "Europe/Berlin"
        os.environ["MIG0100_I_READ_DOCS"] = "YES"

        self.apply_test_relational_schema()

        self.migrate_previous()

        MigrationHelper.load_migrations()
        # Only migrate tested migration in following test.
        patcher = patch(
            "os.listdir",
            return_value=[MigrationHelper.migrations[self.migration_number]],
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def tearDown(self) -> None:
        if MigrationHelper.migrate_thread:
            self.wait_for_migration_thread(15)
            MigrationHelper.migrate_thread = None
        MigrationHelper.migrate_thread_exception = None
        if MigrationHelper.migrate_thread_stream:
            MigrationHelper.close_migrate_thread_stream()
        super().tearDown()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.apply_fresh_relational_schema()
        super().tearDownClass()

    @staticmethod
    def apply_test_relational_schema() -> None:
        """
        Creates old idempotent key-value-store schema and relational schema on top.
        Also deactivates notify triggers.
        """
        with get_new_os_conn() as conn:
            with conn.cursor() as curs:
                curs.execute("DROP SCHEMA public CASCADE;")
                curs.execute("CREATE SCHEMA public;")
                curs.execute(open(DEPR_SQL_PATH).read())

                # Write migration index like legacy migrations expected to apply initial schema correctly.
                curs.execute(
                    f"INSERT INTO positions (timestamp, user_id, migration_index) VALUES ('2026-06-04', 1, {MIN_NON_REL_MIGRATION + 1})"
                )
        create_schema()

    @staticmethod
    def apply_fresh_relational_schema() -> None:
        """
        Creates fresh relational schema and deactivates notify triggers.
        """
        with get_new_os_conn() as conn:
            with conn.cursor() as curs:
                curs.execute("DROP SCHEMA public CASCADE;")
                curs.execute("CREATE SCHEMA public;")
        # Uses current schema because schema is fresh.
        create_schema()
        with get_new_os_conn() as conn:
            with conn.cursor() as curs:
                table_names = get_rel_db_table_names(curs)
                curs.execute(generate_sql_for_test_initiation(tuple(table_names)))
                deactivate_notify_triggers(curs)

    def wait_for_lock(self, wait_lock: Lock, indicator_lock: Lock) -> Callable:
        """
        wait_lock is intended to be waited upon and should be unlocked in the test when needed.
        indicator_lock is used as an indicator that the thread is waiting for the wait_lock and must
        be in locked state.
        Intended for replacing MigrationHelper.write_line by a mock.
        """

        def _wait_for_lock(*args: Any, **kwargs: Any) -> mockdefault:
            assert (
                MigrationHelper.migrate_thread_stream
            ), "migrate_thread_stream not initialized by migration framework."
            if args[0] == "migration started":
                MigrationHelper.migrate_thread_stream.write(args[0] + "\n")
                indicator_lock.release()
                wait_lock.acquire()
            else:
                MigrationHelper.migrate_thread_stream.write(args[0] + "\n")
            return mockdefault

        return _wait_for_lock

    def migrate_previous(self) -> dict[str, Any]:
        """
        Executes the `migrate` command using a MigrationManager.
        Waits for thread execution.
        """
        # Migrate to state before tested migration.
        if filenames := [
            f
            for f in os.listdir(MIGRATIONS_PATH)
            if re.match("mig_\\d+", f[:8]) and int(f[4:8]) < self.migration_number
        ]:
            with patch("os.listdir", return_value=filenames):
                manager = MigrationManager(Mock(), Mock(), Mock())
                result = manager.handle_request({"cmd": "migrate", "verbose": True})
                self.wait_for_migration_thread(15)
                with self.connection.cursor() as curs:
                    MigrationHelper.assert_migration_index(curs)
        else:
            result = {}

        # mimik reset or similar mechanism
        if MigrationHelper.migrate_thread_stream:
            MigrationHelper.migrate_thread_stream.close()
        MigrationHelper.migrate_thread_stream = None
        MigrationHelper.migrate_thread_stream_can_be_closed = False
        MigrationHelper.migrate_thread_exception = None

        return result

    def assert_content_not_none(
        self,
        cur: Cursor[DictRow],
        query: str,
        value: dict[str, Any] | None = None,
        error_message: str = "",
    ) -> None:
        """
        Checks whether the first element of the result for `query` matches `value`.
        `value` should be None if the expected result is just not None.
        Because of this behavior, it can't be compared to an expected result of None.
        If a certain debug error message should be displayed provide error_message.
        """
        result = cur.execute(query).fetchone()
        if error_message:
            assert result, error_message
        else:
            assert result, f"Database did not contain a result for this query.\n{query}"
        if value is not None and result != value:
            raise Exception(
                f"Database did not contain the expected result '{value} vs {result}' for this query.\n{query}"
            )

    def wait_for_migration_thread(self, for_seconds: int) -> None:
        """
        Waits for the thread to terminate and asserts the thread is not alive.
        """
        assert MigrationHelper.migrate_thread
        MigrationHelper.migrate_thread.join(for_seconds)
        assert not MigrationHelper.migrate_thread.is_alive()

    @staticmethod
    def transform_data(data: Any, field: Field | None = None) -> Any:
        """
        Purpose:
            Casts data so it is psycopg friendly in case it is not parsable by psycopg.
            Known and implemented cases:
                - Decimals
                - json (mostly Dictionaries)
                - Timestamps
        Input:
            - data: python formatted data
        Returns:
            - data: psycopg friendly data
        """
        if isinstance(field, DecimalField):
            data = Decimal(data)
        elif isinstance(field, TimestampField):
            data = datetime.fromtimestamp(data, ZoneInfo("UTC"))
        elif isinstance(field, JSONField):
            data = json_dumps(data)

        return data
