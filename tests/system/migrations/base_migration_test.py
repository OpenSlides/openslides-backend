import os
import re
from collections.abc import Callable
from datetime import datetime
from decimal import Decimal
from json import dumps as json_dumps
from threading import Lock
from typing import Any
from unittest import TestCase
from unittest.mock import DEFAULT as mockdefault
from unittest.mock import Mock, patch
from zoneinfo import ZoneInfo

from psycopg import Cursor, sql
from psycopg.rows import DictRow

from meta.dev.src.helper_get_names import HelperGetNames
from openslides_backend.http.application import OpenSlidesBackendWSGIApplication
from openslides_backend.http.views import ActionView
from openslides_backend.migrations.migration_helper import (
    MIGRATIONS_PATH,
    MIN_NON_REL_MIGRATION,
    MigrationHelper,
    MigrationState,
)
from openslides_backend.migrations.migration_manager import MigrationManager
from openslides_backend.models.fields import (
    DecimalField,
    Field,
    JSONField,
    TimestampField,
)
from openslides_backend.services.postgresql.create_schema import create_schema
from openslides_backend.services.postgresql.db_connection_handling import (
    get_new_os_conn,
)
from openslides_backend.services.postgresql.utils import deactivate_notify_triggers
from openslides_backend.shared.exceptions import BadCodingException
from openslides_backend.shared.patterns import (
    FullQualifiedId,
    collection_and_id_from_fqid,
)
from openslides_backend.shared.typing import PartialModel
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID
from tests.conftest import get_rel_db_table_names
from tests.conftest_helper import generate_sql_for_test_initiation
from tests.system.util import create_action_test_application, get_route_path

DEPR_SQL_PATH = os.path.realpath(
    os.path.join(os.getcwd(), "tests", "system", "migrations", "deprecated_schema.sql")
)
MIGRATIONS_URL = get_route_path(ActionView.migrations_route)


class BaseMigrationTestCase(TestCase):
    # has to be set by subclass
    migration_number: int

    # defaults, can be overridden by subclass
    MAX_WAIT = 15

    # internally calculated variables
    migration_dir_list: list[str]
    app: OpenSlidesBackendWSGIApplication

    def setUp(self) -> None:
        """
        Does not call super class to prevent usage of client and so forth.
        """
        # Create services
        self.app = create_action_test_application()

        # Set up state before migration 100

        self.apply_test_relational_schema()

        self.migrate_previous()

        # Only migrate tested migration in following test.
        patcher = patch(
            "os.listdir",
            return_value=self.migration_dir_list,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def cleanup_helper_class(self) -> None:
        if MigrationHelper.migrate_thread:
            self.wait_for_migration_thread(15)
            MigrationHelper.migrate_thread = None
        MigrationHelper.migrate_thread_exception = None
        if MigrationHelper.migrate_thread_stream:
            MigrationHelper.migrate_thread_stream_can_be_closed = True
            MigrationHelper.close_migrate_thread_stream()

    def tearDown(self) -> None:
        self.cleanup_helper_class()
        super().tearDown()

    @classmethod
    def setUpClass(cls) -> None:
        cls.prepare_mig_100_environment()

        cls.migration_dir_list = [
            f
            for f in os.listdir(MIGRATIONS_PATH)
            if re.match("mig_\\d{4}", f[:8]) and int(f[4:8]) <= cls.migration_number
        ]

    @classmethod
    def tearDownClass(cls) -> None:
        for key in ["MIG0100_I_READ_DOCS", "MIG0100_TIMEZONE"]:
            if os.getenv(key):
                del os.environ[key]

        cls.apply_fresh_relational_schema()
        super().tearDownClass()

    def create_migration_manager(self) -> MigrationManager:
        return MigrationManager(Mock(), Mock(), self.app.logging)

    @staticmethod
    def make_migration_request(manager: MigrationManager) -> dict[str, Any]:
        return manager.handle_request({"cmd": "migrate", "verbose": True})

    @staticmethod
    def get_stats(manager: MigrationManager) -> dict[str, Any]:
        return manager.handle_request({"cmd": "stats", "verbose": True})

    def set_up_organization(self) -> None:
        self.create_entries(
            {
                ONE_ORGANIZATION_FQID: {"name": "Intevation", "theme_id": 1},
                "theme/1": {"name": "standard theme"},
            }
        )

    @staticmethod
    def prepare_mig_100_environment() -> None:
        """Sets environment variables required for migration 100"""
        os.environ["MIG0100_TIMEZONE"] = "Europe/Berlin"
        os.environ["MIG0100_I_READ_DOCS"] = "YES"

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
            MigrationHelper.migrate_thread_stream.write(args[0] + "\n")
            if args[0] == "migration started":
                indicator_lock.release()
                wait_lock.acquire()
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
            if re.match("mig_\\d{4}", f[:8]) and int(f[4:8]) < self.migration_number
        ]:
            with patch("os.listdir", return_value=filenames):
                manager = MigrationManager(Mock(), Mock(), Mock())
                result = manager.handle_request({"cmd": "migrate", "verbose": True})
                self.cleanup_helper_class()
                with get_new_os_conn() as conn:
                    with conn.cursor() as curs:
                        MigrationHelper.assert_migration_index(curs)
        else:
            result = {}

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

    def get_migration_state(self) -> MigrationState | None:
        with get_new_os_conn() as conn:
            with conn.cursor() as curs:
                if result := curs.execute(
                    f"SELECT migration_state FROM version WHERE migration_index = {self.migration_number};"
                ).fetchall():
                    return result[0]["migration_state"]
        return None

    def assert_migration_finalized(self) -> None:
        assert MigrationState.FINALIZED == self.get_migration_state()

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

    def create_entries(
        self,
        data: dict[FullQualifiedId, PartialModel],
        intermediate_tables_data: dict[str, list[dict[str, Any]]] = {},
    ) -> None:
        assert data, "data can not be empty"
        with get_new_os_conn() as conn:
            with conn.cursor() as curs:
                for fqid, data in data.items():
                    assert data, "data can not contain empty dictionaries"
                    collection, id_ = collection_and_id_from_fqid(fqid)
                    table_name = HelperGetNames.get_table_name(collection)
                    model_data = {**data, "id": id_}
                    curs.execute(
                        sql.SQL(
                            "INSERT INTO {table_name} ({columns}) VALUES ({values});"
                        ).format(
                            table_name=sql.Identifier(table_name),
                            columns=sql.SQL(", ").join(
                                sql.Identifier(column) for column in model_data.keys()
                            ),
                            values=sql.SQL(", ").join(
                                sql.Placeholder() for _ in model_data
                            ),
                        ),
                        [*model_data.values()],
                    )
                if intermediate_tables_data:
                    self.write_into_intermediate_table(curs, intermediate_tables_data)
                conn.commit()

    def update_entries(
        self,
        tables_data: dict[FullQualifiedId, PartialModel],
        intermediate_tables_data: dict[str, list[dict[str, Any]]] = {},
    ) -> None:
        assert tables_data, "data can not be empty"
        with get_new_os_conn() as conn:
            with conn.cursor() as curs:
                for fqid, collection_data in tables_data.items():
                    assert collection_data, "data can not contain empty dictionaries"
                    collection, id_ = collection_and_id_from_fqid(fqid)
                    table_name = HelperGetNames.get_table_name(collection)
                    if len(tables_data) == 1:
                        set_part = sql.SQL("{column} = {placeholder}").format(
                            column=sql.Identifier(list(tables_data.keys())[0]),
                            placeholder=sql.Placeholder(),
                        )
                    else:
                        set_part = sql.SQL("({columns}) = ({placeholders})").format(
                            columns=sql.SQL(", ").join(
                                sql.Identifier(column) for column in tables_data.keys()
                            ),
                            placeholders=sql.SQL(", ").join(
                                sql.Placeholder() for _ in tables_data
                            ),
                        )
                    curs.execute(
                        sql.SQL("UPDATE {table_name} {set_part} WHERE id={id}").format(
                            table_name=sql.Identifier(table_name),
                            set_part=set_part,
                            id=sql.Placeholder(),
                        ),
                        [*tables_data.values(), id_],
                    )
                if intermediate_tables_data:
                    self.write_into_intermediate_table(curs, intermediate_tables_data)
                conn.commit()

    @staticmethod
    def write_into_intermediate_table(
        curs: Cursor[DictRow],
        intermediate_tables_data: dict[str, list[dict[str, Any]]],
    ) -> None:
        for table_name, data in intermediate_tables_data.items():
            column_names = data[0].keys()
            if not all(item.keys() == column_names for item in data[1:]):
                raise BadCodingException("All the keys in 'data' must be the same.")
            curs.execute(
                sql.SQL("INSERT INTO {table} ({columns}) VALUES {values};").format(
                    table=sql.Identifier(table_name),
                    columns=sql.SQL(", ").join(
                        sql.Identifier(column) for column in column_names
                    ),
                    values=sql.SQL(", ").join(
                        sql.SQL("({values_placeholders})").format(
                            values_placeholders=sql.SQL(", ").join(
                                sql.Placeholder() for _ in column_names
                            )
                        )
                        for _ in data
                    ),
                ),
                [
                    target_value
                    for data_item in data
                    for target_value in data_item.values()
                ],
            )
