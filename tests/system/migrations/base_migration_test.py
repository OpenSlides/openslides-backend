from unittest import TestCase

from openslides_backend.migrations.migration_handler import MigrationHandler
from openslides_backend.migrations.migration_helper import MigrationHelper


class BaseMigrationTestCase(TestCase):
    def tearDown(self) -> None:
        MigrationHelper.table_translations = dict()
        MigrationHelper.migrate_thread = None
        MigrationHelper.migrate_thread_exception = None
        MigrationHelper.migrate_thread_stream_read_pos = 0
        MigrationHelper.migrate_thread_stream_just_read = False
        if MigrationHelper.migrate_thread_stream:
            MigrationHandler.close_migrate_thread_stream()
        super().tearDown()

    def wait_for_migration_thread(self, for_seconds: int) -> None:
        """
        Waits for the thread to terminate and asserts the thread is not alive.
        """
        assert MigrationHelper.migrate_thread
        MigrationHelper.migrate_thread.join(for_seconds)
        assert not MigrationHelper.migrate_thread.is_alive()
