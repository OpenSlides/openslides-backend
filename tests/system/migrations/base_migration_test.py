from datetime import datetime
from decimal import Decimal
from json import dumps as json_dumps
from typing import Any
from unittest.mock import patch
from zoneinfo import ZoneInfo

from psycopg import Cursor
from psycopg.rows import DictRow

from openslides_backend.migrations.migration_handler import MigrationHandler
from openslides_backend.migrations.migration_helper import MigrationHelper
from openslides_backend.models.fields import (
    DecimalField,
    Field,
    JSONField,
    TimestampField,
)
from tests.system.base import BaseSystemTestCase


class BaseMigrationTestCase(BaseSystemTestCase):
    # has to be set by subclass
    migration_file: str

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

        # mock the return value
        cls.patcher = patch("os.listdir", return_value=[cls.migration_file])
        # start the patch
        cls.patcher.start()
        # stop after all tests
        cls.addClassCleanup(cls.patcher.stop)

    def setUp(self) -> None:
        """
        Does not call super class to prevent usage of client and so forth.
        """
        self.used_collections = set()
        self.created_fqids: set[str] = set()
        self.deleted_fqids: set[str] = set()

    def tearDown(self) -> None:
        MigrationHelper.migrate_thread = None
        MigrationHelper.migrate_thread_exception = None
        MigrationHelper.migrate_thread_stream_read_pos = 0
        MigrationHelper.migrate_thread_stream_just_read = False
        if MigrationHelper.migrate_thread_stream:
            MigrationHandler.close_migrate_thread_stream()
        super().tearDown()

    def assert_content_not_none(
        self,
        cur: Cursor[DictRow],
        query: str,
        value: dict[str:Any] | None = None,
        error_message: str = "",
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
            assert result, f"Database did not contain a result for this query.\n{query}"
        if value is not None:
            assert result == value

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
