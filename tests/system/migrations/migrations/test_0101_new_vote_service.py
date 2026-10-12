from openslides_backend.migrations.migration_helper import MigrationState
from openslides_backend.shared.exceptions import BadCodingException
from openslides_backend.shared.patterns import FullQualifiedId
from openslides_backend.shared.typing import PartialModel
from tests.system.migrations.base_migration_test import BaseMigrationTestCase

DEFAULT_PROJECTOR_OPTIONS = (
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


class TestMigration101(BaseMigrationTestCase):
    migration_number = 101
    EXPECTED_INTRODUCTION = ""

    @staticmethod
    def _get_meeting_data(
        base: int = 1, meeting_data: PartialModel = {}
    ) -> dict[FullQualifiedId, PartialModel]:
        data: dict[FullQualifiedId, PartialModel] = {}
        if "committee_id" not in meeting_data:
            committee_id = base + 59
            meeting_data["committee_id"] = committee_id
            data[f"committee/{committee_id}"] = {"name": f"Committee {committee_id}"}
        data.update(
            {
                f"meeting/{base}": {
                    "default_group_id": base,
                    "admin_group_id": base + 1,
                    "motions_default_workflow_id": base,
                    "motions_default_amendment_workflow_id": base,
                    "reference_projector_id": base,
                    "committee_id": committee_id,
                    "is_active_in_organization_id": 1,
                    "language": "en",
                    **meeting_data,
                },
                f"projector/{base}": {
                    "meeting_id": base,
                    "name": f"Projector {base}",
                    **{
                        f"used_as_default_projector_for_{option}_in_meeting_id": base
                        for option in DEFAULT_PROJECTOR_OPTIONS
                    },
                },
                f"group/{base}": {"meeting_id": base, "name": f"group{base}"},
                f"group/{base+1}": {"meeting_id": base, "name": f"group{base+1}"},
                f"group/{base+2}": {"meeting_id": base, "name": f"group{base+2}"},
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
            }
        )
        return data

    def test_migration_manager(self) -> None:
        origin_data: dict[FullQualifiedId, PartialModel] = self._get_meeting_data(
            1,
            {
                "motion_poll_projection_name_order_first": "first_name",
                "motion_poll_projection_max_columns": 8,
                # "assignment_poll_default_group_ids": [1],
                # "motion_poll_default_group_ids": [3],
                # "topic_poll_default_group_ids": [4],
                "assignment_poll_default_method": "Y",
                "motion_poll_default_method": "YNA",
                "poll_default_method": "N",
                "assignment_poll_default_type": "named",
                "motion_poll_default_type": "open",
                "poll_default_type": "analog",
                "assignment_poll_default_onehundred_percent_base": "YNA",
                "motion_poll_default_onehundred_percent_base": "valid",
                "poll_default_onehundred_percent_base": "valid",
                "assignment_poll_sort_poll_result_by_votes": False,
                "assignment_poll_enable_max_votes_per_option": True,
                "poll_sort_poll_result_by_votes": True,
                "poll_default_live_voting_enabled": True,
            },
        )
        origin_data["group/1"]["permissions"] = ["poll.can_manage"]
        origin_data["group/2"]["permissions"] = [
            "poll.can_manage",
            "motion.can_manage_polls",
        ]
        origin_data["group/3"]["permissions"] = ["motion.can_see", "mediafile.can_see"]
        origin_data["group/4"] = {"meeting_id": 1, "name": "group4", "permissions": []}

        self.set_up_organization()
        self.create_entries(origin_data)

        result = self.make_migration_request()
        if result["status"] == MigrationState.MIGRATION_FAILED:
            raise BadCodingException(
                f"Migration failed with message: {result['exception']}."
            )
        self.assertEqual(result["status"], MigrationState.MIGRATION_RUNNING)
        self.wait_for_migration_thread(self.MAX_WAIT)
