import json
import os
from importlib import import_module
from typing import Any
from unittest.mock import Mock

from openslides_backend.migrations.migration_helper import (
    MigrationHelper,
    MigrationState,
)
from openslides_backend.migrations.migration_manager import MigrationManager
from openslides_backend.models.base import model_registry
from openslides_backend.services.postgresql.db_connection_handling import os_conn_pool
from openslides_backend.shared.patterns import (
    FullQualifiedId,
    fqid_from_collection_and_id,
)
from openslides_backend.shared.typing import Model
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

    def setUp(self) -> None:
        super().setUp()
        data: dict[FullQualifiedId, Model] = dict()

        with os_conn_pool.connection() as conn:
            with conn.cursor() as curs:
                # 4.D1) clears models table
                curs.execute("TRUNCATE TABLE organization_t CASCADE;")
                curs.execute("TRUNCATE TABLE version;")

        with open(EXAMPLE_DATA_PATH) as file:
            raw_data: dict[str, Any] = json.loads(file.read())

        for collection, models in raw_data.items():
            if collection == "_migration_index":
                continue
            self.used_collections.add(collection)
            for model_id, model in models.items():
                data[fqid_from_collection_and_id(collection, model_id)] = {
                    f: self.transform_data(
                        v, model_registry[collection]().try_get_field(f)
                    )
                    for f, v in model.items()
                    if not f.startswith("meta_")
                }
        self.set_models(data)

        # TODO this step is probably equal for all tests # TODO should be done for all previous # TODO just use mig number for this
        with os_conn_pool.connection() as conn:
            with conn.cursor() as curs:
                MigrationHelper.set_database_migration_info(
                    curs, 100, MigrationState.FINALIZED
                )

    def test_simple(self) -> None:
        manager = MigrationManager(Mock(), Mock(), Mock())
        assert manager.handle_request({"cmd": "finalize", "verbose": True}) == {
            "output": "migration started\n",
            "status": MigrationState.MIGRATION_RUNNING,
        }

        assert manager.handle_request({"cmd": "stats", "verbose": True}) == {
            "stats": {
                "current_migration_index": 100,
                "target_migration_index": 101,
                "status": MigrationState.MIGRATION_RUNNING,
                "output": "migration started\n",
                "migratable_models": {
                    "assignment": 2,
                    "assignment_candidate": 5,
                    "meeting": 1,
                    "meeting_user": 3,
                },
            },
        }
        self.wait_for_migration_thread(15)
        assert manager.handle_request({"cmd": "stats", "verbose": True}) == {
            "stats": {
                "current_migration_index": 101,
                "target_migration_index": 101,
                "status": MigrationState.FINALIZED,
                "output": "migration started\nmigration finished\nfinalization started\nfinalization finished\n",
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
        self.assert_model_exists("meeting/1", {"motions_number_type": None})
