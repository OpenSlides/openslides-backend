from openslides_backend.services.postgresql.db_connection_handling import (
    get_new_os_conn,
)
from tests.system.migrations.base_migration_test import (
    AssertFieldData,
    BaseMigrationTestCase,
)

from .test_0102_consultation_sequence_setting import (
    get_fk_constraint_name_condition,
    get_meeting_data,
)


class TestMigration103(BaseMigrationTestCase):
    migration_number = 103

    def get_find_fk_constraint_name_condition(self, field_data: AssertFieldData) -> str:
        return get_fk_constraint_name_condition(field_data)

    def test_0103(self) -> None:
        self.set_up_organization()
        self.create_entries(get_meeting_data())
        manager = self.create_migration_manager()

        self.make_migration_request(manager)
        self.wait_for_migration_thread(self.MAX_WAIT)

        self.assert_migration_finalized()

        self.create_entries(get_meeting_data(4))

        with get_new_os_conn() as conn:
            with conn.cursor() as curs:
                self.assert_field_exists(
                    curs, "meeting_t", "enable_idm_matching", "boolean", default="false"
                )
                self.assert_view_exists(curs, "meeting")

                self.assert_field_exists(
                    curs,
                    "committee_t",
                    "identity_key",
                    "character varying",
                    max_len=256,
                )
                self.assert_view_exists(curs, "committee")

                self.assert_field_exists(
                    curs,
                    "organization_t",
                    "idm_identity_key",
                    "character varying",
                    max_len=256,
                )
                self.assert_field_exists(
                    curs,
                    "organization_t",
                    "idm_organization_managment_key",
                    "character varying",
                    max_len=256,
                )
                self.assert_field_exists(
                    curs,
                    "organization_t",
                    "idm_committee_management_key",
                    "character varying",
                    max_len=256,
                )
                self.assert_view_exists(curs, "organization")

                table_fields = self.assert_table_fields(
                    curs, "idm_condition_t", ["id", "idm_field", "regex", "mapper_id"]
                )
                self.assert_id_field_exists(curs, "idm_condition_t", table_fields)
                self.assert_field_exists(
                    curs,
                    "idm_condition_t",
                    "idm_field",
                    "character varying",
                    table_fields,
                    is_nullable=False,
                    max_len=256,
                )
                self.assert_field_exists(
                    curs,
                    "idm_condition_t",
                    "regex",
                    "character varying",
                    table_fields,
                    is_nullable=False,
                    max_len=256,
                )
                self.assert_field_exists(
                    curs,
                    "idm_condition_t",
                    "mapper_id",
                    "integer",
                    table_fields,
                    is_nullable=False,
                    fk_to_table_name="idm_mapper_t",
                )
                self.assert_view_exists(curs, "idm_condition")
                self.assert_trigger_exists(curs, "tr_log_idm_condition")
                self.assert_trigger_exists(curs, "tr_log_idm_condition_mapper_id")

                table_fields = self.assert_table_fields(
                    curs,
                    "idm_mapper_t",
                    ["id", "group_external_ids", "weight", "organization_id"],
                )
                self.assert_id_field_exists(curs, "idm_mapper_t", table_fields)
                self.assert_field_exists(
                    curs,
                    "idm_mapper_t",
                    "group_external_ids",
                    "ARRAY",
                    table_fields,
                    is_nullable=False,
                )
                self.assert_field_exists(
                    curs,
                    "idm_mapper_t",
                    "weight",
                    "integer",
                    table_fields,
                    default="10000",
                )
                self.assert_field_exists(
                    curs,
                    "idm_mapper_t",
                    "organization_id",
                    "integer",
                    table_fields,
                    is_nullable=False,
                    fk_to_table_name="organization_t",
                    default="1",
                )
                self.assert_view_exists(curs, "idm_mapper")
                self.assert_trigger_exists(curs, "tr_log_idm_mapper")
                self.assert_trigger_exists(curs, "tr_log_idm_mapper_organization_id")
                self.assert_trigger_exists(
                    curs, "tr_constant_idm_mapper_organization_id"
                )

                table_fields = self.assert_table_fields(
                    curs,
                    "idm_mapping_t",
                    [
                        "id",
                        "idm_field",
                        "os_field",
                        "default_value",
                        "allow_update",
                        "override_default",
                        "mapper_id",
                    ],
                )
                self.assert_id_field_exists(curs, "idm_mapping_t", table_fields)
                self.assert_field_exists(
                    curs,
                    "idm_mapping_t",
                    "idm_field",
                    "character varying",
                    table_fields,
                    is_nullable=False,
                    max_len=256,
                )
                self.assert_enum_exists(
                    curs,
                    "enum_idm_mapping_os_field",
                    [
                        "structure_level_ids",
                        "number",
                        "vote_weight",
                        "present",
                        "comment",
                    ],
                )
                self.assert_field_exists(
                    curs,
                    "idm_mapping_t",
                    "os_field",
                    "USER-DEFINED",
                    table_fields,
                    is_nullable=False,
                    enum_name="enum_idm_mapping_os_field",
                )
                self.assert_field_exists(
                    curs,
                    "idm_mapping_t",
                    "default_value",
                    "character varying",
                    table_fields,
                    max_len=256,
                )
                self.assert_field_exists(
                    curs, "idm_mapping_t", "allow_update", "boolean", table_fields
                )
                self.assert_field_exists(
                    curs, "idm_mapping_t", "override_default", "boolean", table_fields
                )
                self.assert_field_exists(
                    curs,
                    "idm_mapping_t",
                    "mapper_id",
                    "integer",
                    table_fields,
                    is_nullable=False,
                    fk_to_table_name="idm_mapper_t",
                )
                self.assert_view_exists(curs, "idm_mapping")
                self.assert_trigger_exists(curs, "tr_log_idm_mapping")
                self.assert_trigger_exists(curs, "tr_log_idm_mapping_mapper_id")

                # check if default is applied to both old meetings (1)
                # and meetings created after the migration is finalized (4).
                assert (
                    curs.execute(
                        "SELECT id, enable_idm_matching FROM meeting_t;"
                    ).fetchall()
                ) == [
                    {"id": 1, "enable_idm_matching": False},
                    {"id": 4, "enable_idm_matching": False},
                ]
