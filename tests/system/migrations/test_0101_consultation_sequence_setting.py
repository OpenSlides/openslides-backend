from openslides_backend.migrations.migration_helper import MigrationState
from openslides_backend.services.postgresql.db_connection_handling import (
    get_new_os_conn,
)
from openslides_backend.shared.exceptions import BadCodingException
from openslides_backend.shared.patterns import FullQualifiedId
from openslides_backend.shared.typing import PartialModel
from tests.system.migrations.base_migration_test import BaseMigrationTestCase


def get_meeting_data(base: int = 1) -> dict[FullQualifiedId, PartialModel]:
    return {
        f"meeting/{base}": {
            "default_group_id": base,
            "admin_group_id": base + 1,
            "motions_default_workflow_id": base,
            "motions_default_amendment_workflow_id": base,
            "reference_projector_id": base,
            "committee_id": 59 + base,
            "is_active_in_organization_id": 1,
            "language": "en",
        },
        f"projector/{base}": {
            "meeting_id": base,
            "name": f"Projector {base}",
            **{
                f"used_as_default_projector_for_{option}_in_meeting_id": base
                for option in (
                    "agenda_item_list",
                    "topic",
                    "list_of_speakers",
                    "current_los",
                    "motion",
                    "amendment",
                    "motion_block",
                    "assignment",
                    "mediafile",
                    "message",
                    "countdown",
                    "assignment_poll",
                    "motion_poll",
                    "poll",
                )
            },
        },
        f"group/{base}": {"meeting_id": base, "name": "group1"},
        f"group/{base+1}": {"meeting_id": base, "name": "group2"},
        f"group/{base+2}": {"meeting_id": base, "name": "group3"},
        f"motion_workflow/{base}": {
            "name": "flo",
            "meeting_id": base,
            "first_state_id": base,
        },
        f"motion_state/{base}": {
            "name": "stasis",
            "weight": 36,
            "meeting_id": base,
            "workflow_id": base,
        },
        f"committee/{59+base}": {"name": f"Committee{59+base}"},
    }


class TestMigration101(BaseMigrationTestCase):
    migration_number = 101

    def test_0101(self) -> None:

        self.set_up_organization()
        self.create_entries(get_meeting_data())
        manager = self.create_migration_manager()

        intermediate_result = self.make_migration_request(manager)
        if intermediate_result["status"] == MigrationState.MIGRATION_FAILED:
            raise BadCodingException(
                "Migration failed with message: {intermediate_result['exception']}."
            )
        if intermediate_result["status"] == MigrationState.MIGRATION_RUNNING:
            self.wait_for_migration_thread(self.MAX_WAIT)
        else:
            self.assertEqual(intermediate_result["status"], MigrationState.FINALIZED)

        self.assert_migration_finalized()

        self.create_entries(get_meeting_data(4))
        with get_new_os_conn() as conn:
            with conn.cursor() as curs:
                assert (
                    col_data := curs.execute(
                        "SELECT * FROM information_schema.columns WHERE table_name='meeting_t' AND column_name='motions_enable_consultation_sequence';"
                    ).fetchone()
                )
                # check if field exists and has the correct settings
                self.assert_contained_in(
                    {
                        "table_name": "meeting_t",
                        "column_name": "motions_enable_consultation_sequence",
                        "data_type": "boolean",
                        "column_default": "true",
                        "is_nullable": "YES",
                        "is_updatable": "YES",
                        # I never ever will desert you when your heart is torn
                        "is_self_referencing": "NO",
                        "is_identity": "NO",
                        "is_generated": "NEVER",
                    },
                    col_data,
                )
                # check if default is not applied to old meetings (1)
                # but meetings created after the migration is finalized (4) should have it.
                assert (
                    curs.execute(
                        "SELECT id, motions_enable_consultation_sequence FROM meeting_t;"
                    ).fetchall()
                ) == [
                    {"id": 1, "motions_enable_consultation_sequence": False},
                    {"id": 4, "motions_enable_consultation_sequence": True},
                ]
