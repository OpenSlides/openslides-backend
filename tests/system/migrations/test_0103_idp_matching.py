from openslides_backend.migrations.migration_helper import MigrationState
from openslides_backend.services.postgresql.db_connection_handling import (
    get_new_os_conn,
)
from openslides_backend.shared.exceptions import BadCodingException
from tests.system.migrations.base_migration_test import BaseMigrationTestCase

from .test_0102_consultation_sequence_setting import get_meeting_data


class TestMigration103(BaseMigrationTestCase):
    migration_number = 103

    def test_0103(self) -> None:
        self.set_up_organization()
        self.create_entries(get_meeting_data())
        manager = self.create_migration_manager()

        intermediate_result = self.make_migration_request(manager)
        if intermediate_result["status"] == MigrationState.MIGRATION_FAILED:
            raise BadCodingException(
                f"Migration failed with message: {intermediate_result['exception']}."
            )
        if intermediate_result["status"] != MigrationState.FINALIZED:
            self.wait_for_migration_thread(self.MAX_WAIT)

        self.assert_migration_finalized()

        self.create_entries(get_meeting_data(4))
        with get_new_os_conn() as conn:
            with conn.cursor() as curs:
                for tablename, fname, datatype, default, max_len in [
                    ("meeting_t", "enable_idp_matching", "boolean", "false", None),
                    ("committee_t", "identity_key", "character varying", None, 256),
                    (
                        "organization_t",
                        "idp_identity_key",
                        "character varying",
                        None,
                        256,
                    ),
                ]:
                    assert (
                        col_data := curs.execute(
                            f"SELECT * FROM information_schema.columns WHERE table_name='{tablename}' AND column_name='{fname}';"
                        ).fetchone()
                    )
                    # check if field exists and has the correct settings
                    self.assert_contained_in(
                        {
                            "table_name": tablename,
                            "column_name": fname,
                            "data_type": datatype,
                            "column_default": default,
                            "is_nullable": "YES",
                            "is_updatable": "YES",
                            "is_self_referencing": "NO",
                            "is_identity": "NO",
                            "is_generated": "NEVER",
                            "character_maximum_length": max_len,
                        },
                        col_data,
                    )
                for tablename, fnames in {
                    "idp_condition_t": [
                        "id",
                        "idp_field",
                        "regex",
                        "mapper_id",
                    ],
                    "idp_mapper_t": [
                        "id",
                        "group_external_ids",
                        "weight",
                        "organization_id",
                    ],
                    "idp_mapping_t": [
                        "id",
                        "idp_field",
                        "os_field",
                        "default_value",
                        "allow_update",
                        "override_default",
                        "mapper_id",
                    ],
                }.items():
                    cols = curs.execute(
                        f"SELECT * FROM information_schema.columns WHERE table_name='{tablename}';"
                    ).fetchall()
                    assert sorted(col["column_name"] for col in cols) == sorted(fnames)

                # TODO: check schema for enums, field types etc, views and triggers

                # check if default is applied to both old meetings (1)
                # and meetings created after the migration is finalized (4).
                assert (
                    curs.execute(
                        "SELECT id, enable_idp_matching FROM meeting_t;"
                    ).fetchall()
                ) == [
                    {"id": 1, "enable_idp_matching": False},
                    {"id": 4, "enable_idp_matching": False},
                ]
