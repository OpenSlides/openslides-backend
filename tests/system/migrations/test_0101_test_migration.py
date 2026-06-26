import os
from collections.abc import Callable
from importlib import import_module
from threading import Lock
from typing import Any
from unittest.mock import DEFAULT as mockdefault
from unittest.mock import Mock, patch

from openslides_backend.migrations.migration_helper import (
    MigrationHelper,
    MigrationState,
)
from openslides_backend.migrations.migration_manager import MigrationManager
from openslides_backend.services.postgresql.db_connection_handling import os_conn_pool
from tests.system.migrations.base_migration_test import BaseMigrationTestCase

migration_module = import_module(
    "openslides_backend.migrations.migrations.0101_test_migration"
)
EXAMPLE_DATA_PATH = os.path.realpath(
    os.path.join(
        os.getcwd(), "tests", "system", "migrations", "legacy-example-data.json"
    )
)


class TestMigration101(BaseMigrationTestCase):
    """
    TODO: This is not an actual valid migration with intended migration activities.
    It is a development thing.
    A place to check if everything works as intended.
    Do NOT merge it into main.
    """

    migration_file = "0101_test_migration.py"

    # def setUp(self) -> None:
    #     """For a real test the data should be more precise of course."""
    #     super().setUp()
    #     data: dict[FullQualifiedId, Model] = dict()

    #     with open(EXAMPLE_DATA_PATH) as file:
    #         raw_data: dict[str, Any] = json.loads(file.read())

    #     model_registry["assignment_category"] = model_registry.pop("assignment_candidate")
    #     for collection, models in raw_data.items():
    #         if collection == "_migration_index":
    #             continue
    #         if collection == "assignment_candidate":
    #             collection = "assignment_category"
    #         for model_id, model in models.items():
    #             data[fqid_from_collection_and_id(collection, model_id)] = {
    #                 f: self.transform_data(
    #                     v, model_registry[collection]().try_get_field(f)
    #                 )
    #                 for f, v in model.items()
    #                 if not f.startswith("meta_")
    #                 if not f == "motions_number_type"
    #             }
    #     model_registry["assignment_candidate"] = model_registry.pop("assignment_category")
    #     self.set_models(data)
    def wait_for_lock(self, wait_lock: Lock, indicator_lock: Lock) -> Callable:
        """
        wait_lock is intended to be waited upon and should be unlocked in the test when needed.
        indicator_lock is used as an indicator that the thread is waiting for the wait_lock and must
        be in locked state.
        Intended for use of a function being wrapped instead of replaced by a mock.
        """

        def _wait_for_lock(*args: Any, **kwargs: Any) -> mockdefault:
            if args[0] == "migration started":
                MigrationHelper.migrate_thread_stream.write("migration started\n")
                indicator_lock.release()
                wait_lock.acquire()
            else:
                MigrationHelper.migrate_thread_stream.write(args[0] + "\n")
            return mockdefault

        return _wait_for_lock

    # @patch(
    #     "openslides_backend.migrations.migration_handler.MigrationHandler.execute_migrations",
    #     wraps=MigrationHandler.execute_migrations,
    # )
    @patch(
        "openslides_backend.migrations.migration_helper.MigrationHelper.write_line",
        # wraps=MigrationHelper.write_line,
    )
    def test_simple(self, method_mock: Mock) -> None:
        wait_lock = Lock()
        wait_lock.acquire()
        indicator_lock = Lock()
        indicator_lock.acquire()
        method_mock.side_effect = self.wait_for_lock(wait_lock, indicator_lock)

        manager = MigrationManager(Mock(), Mock(), Mock())
        assert manager.handle_request({"cmd": "migrate", "verbose": True}) == {
            "output": "migration started\n",
            "status": MigrationState.MIGRATION_RUNNING,
        }

        indicator_lock.acquire()

        with self.connection.cursor() as curs:
            # Assert table and view exist meaning diff got applied.
            assert curs.execute("select * from assignment_category;")
        assert manager.handle_request({"cmd": "stats", "verbose": True}) == {
            "stats": {
                "current_migration_index": 100,
                "target_migration_index": 101,
                "status": MigrationState.MIGRATION_RUNNING,
                "output": "migration started\n",
                "migratable_models": {},
                # "migratable_models": {
                #     "assignment": 2,
                #     "assignment_candidate": 5,
                #     "meeting": 1,
                #     "meeting_user": 3,
                # },
            },
        }

        wait_lock.release()
        self.wait_for_migration_thread(15)

        assert manager.handle_request({"cmd": "stats", "verbose": True}) == {
            "stats": {
                "current_migration_index": 101,
                "target_migration_index": 101,
                "status": MigrationState.FINALIZED,
                "output": "migration started\nmigration finished\n",
                "migratable_models": {},
            },
        }
        with os_conn_pool.connection() as conn:
            with conn.cursor() as curs:
                MigrationHelper.assert_migration_index(curs)
                # 6.8 Recreated foreign key constraints for tables adjacent to mig tables
                self.assert_content_not_none(
                    curs,
                    """SELECT 1
                    FROM information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage AS ccu
                        ON ccu.constraint_name = tc.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                        AND tc.table_name = 'committee_t'
                        AND ccu.table_name = 'meeting_t'
                        AND kcu.column_name = 'default_meeting_id'
                        AND ccu.column_name = 'id'
                        AND tc.constraint_name = 'fk_committee_t_default_meeting_id_meeting_t_id';""",
                )
                self.assert_content_not_none(
                    curs,
                    "SELECT 1 FROM pg_indexes where indexname='idx_committee_t_default_meeting_id';",
                )
                self.assert_content_not_none(
                    curs,
                    """SELECT EXISTS (
                        SELECT * FROM information_schema.tables
                        WHERE table_name = 'assignment_candidate_t'
                    )
                    """,
                    value={"exists": False},
                )
        # self.assert_model_exists("meeting/1", {"motions_number_type": None})
