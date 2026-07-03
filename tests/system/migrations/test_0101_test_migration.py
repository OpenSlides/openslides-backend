import os
from threading import Lock
from unittest.mock import Mock, patch

from openslides_backend.migrations.migration_helper import (
    MigrationHelper,
    MigrationState,
)
from openslides_backend.migrations.migration_manager import MigrationManager
from openslides_backend.services.postgresql.db_connection_handling import os_conn_pool
from tests.system.migrations.base_migration_test import BaseMigrationTestCase

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

    migration_number = 101

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

    @patch(
        "openslides_backend.migrations.migration_helper.MigrationHelper.write_line",
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

                # Assert table and view exist meaning diff got applied.
                self.assert_content_not_none(
                    curs,
                    """SELECT EXISTS (
                        SELECT * FROM information_schema.tables
                        WHERE table_name = 'assignment_candidate_t'
                    )
                    """,
                )
                assert curs.execute("select * from assignment_category;")
        # self.assert_model_exists("meeting/1", {"motions_number_type": None})
