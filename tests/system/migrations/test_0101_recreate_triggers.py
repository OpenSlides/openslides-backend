from openslides_backend.migrations.migration_helper import MigrationState
from openslides_backend.services.postgresql.db_connection_handling import (
    get_new_os_conn,
)
from openslides_backend.shared.exceptions import BadCodingException
from tests.system.migrations.base_migration_test import BaseMigrationTestCase


class TestMigration101(BaseMigrationTestCase):
    migration_number = 101

    def test_0101(self) -> None:

        self.set_up_organization()
        with get_new_os_conn() as conn:
            with conn.cursor() as curs:
                # Introduce some arbitrary changes to the triggers, to see if they're fully reverted to standard build by the migration
                curs.execute("""
CREATE TRIGGER tr_log_a_bit_too_much AFTER INSERT OR UPDATE OF model_id_user_id OR DELETE ON history_entry_t
FOR EACH ROW EXECUTE FUNCTION log_modified_related_models('user','model_id_user_id','history_entry_ids');
""")
                curs.execute(
                    "DROP TRIGGER tr_constant_speaker_meeting_id ON speaker_t;"
                )
                self.assert_trigger_exists(curs, "tr_log_a_bit_too_much")
                self.assert_trigger_not_exists(curs, "tr_constant_speaker_meeting_id")
        manager = self.create_migration_manager()

        intermediate_result = self.make_migration_request(manager)
        if intermediate_result["status"] == MigrationState.MIGRATION_FAILED:
            raise BadCodingException(
                f"Migration failed with message: {intermediate_result['exception']}."
            )
        if intermediate_result["status"] == MigrationState.MIGRATION_RUNNING:
            self.wait_for_migration_thread(self.MAX_WAIT)
        else:
            self.assertEqual(intermediate_result["status"], MigrationState.FINALIZED)

        self.assert_migration_finalized()

        with get_new_os_conn() as conn:
            with conn.cursor() as curs:
                self.assert_trigger_not_exists(curs, "tr_log_a_bit_too_much")
                self.assert_trigger_exists(curs, "tr_constant_speaker_meeting_id")
                # make sure new triggers were created
                for trigger_name in [
                    "tr_log_i_committee_user_ids_from_meeting_t",
                    "tr_log_d_committee_user_ids_from_meeting_t",
                    "tr_log_i_user_committee_ids_from_meeting_t",
                    "tr_log_d_user_committee_ids_from_meeting_t",
                ]:
                    self.assert_trigger_exists(curs, trigger_name)
