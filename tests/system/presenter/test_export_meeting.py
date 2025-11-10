from time import time
from openslides_backend.shared.typing import PartialModel
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID

from openslides_backend.action.action_worker import ActionWorkerState
from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.models.models import Poll, Meeting
from .base import BasePresenterTestCase


class TestExportMeeting(BasePresenterTestCase):
    # 2 temporary test methods. Will be in base class after fixing presenter tests
    def create_meeting(self, base: int = 1, meeting_data: PartialModel = {}) -> None:
        """
        Creates meeting with id 1, committee 60 and groups with ids 1(Default), 2(Admin), 3 by default.
        With base you can setup other meetings, but be cautious because of group-ids
        The groups have no permissions and no users by default.
        """
        committee_id = base + 59
        self.set_models(
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
                    "sequential_number": base,
                    "meeting_id": base,
                    **{field: base for field in Meeting.reverse_default_projectors()},
                },
                f"group/{base}": {"meeting_id": base, "name": f"group{base}"},
                f"group/{base+1}": {"meeting_id": base, "name": f"group{base+1}"},
                f"group/{base+2}": {"meeting_id": base, "name": f"group{base+2}"},
                f"motion_workflow/{base}": {
                    "name": "flo",
                    "sequential_number": base,
                    "meeting_id": base,
                    "first_state_id": base,
                },
                f"motion_state/{base}": {
                    "name": "stasis",
                    "weight": 36,
                    "meeting_id": base,
                    "workflow_id": base,
                    "first_state_of_workflow_id": base,
                },
                f"committee/{committee_id}": {"name": f"Committee{committee_id}"},
                ONE_ORGANIZATION_FQID: {"enable_electronic_voting": True},
            }
        )

    def create_motion(
        self,
        meeting_id: int,
        base: int = 1,
        state_id: int = 0,
        motion_data: PartialModel = {},
    ) -> None:
        """
        The meeting and motion_state must already exist.
        Creates a motion with id 1 by default.
        You can specify another id by setting base.
        If no state_id is passed, meeting must have `state_id` equal to `id`.
        """
        self.set_models(
            {
                f"motion/{base}": {
                    "title": f"motion{base}",
                    "sequential_number": base,
                    "state_id": state_id or meeting_id,
                    "meeting_id": meeting_id,
                    **motion_data,
                },
                f"list_of_speakers/{base}": {
                    "content_object_id": f"motion/{base}",
                    "sequential_number": base,
                    "meeting_id": meeting_id,
                },
            }
        )

    def test_correct(self) -> None:
        self.set_models({"meeting/1": {"name": "test_foo"}})
        status_code, data = self.request("export_meeting", {"meeting_id": 1})
        self.assertEqual(status_code, 200)
        assert data["meeting"]["1"]["name"] == "test_foo"
        for collection in (
            "group",
            "personal_note",
            "tag",
            "agenda_item",
            "list_of_speakers",
            "speaker",
            "topic",
            "motion",
            "motion_submitter",
            "motion_comment",
            "motion_comment_section",
            "motion_category",
            "motion_block",
            "motion_change_recommendation",
            "motion_state",
            "motion_workflow",
            "poll",
            "vote",
            "assignment",
            "assignment_candidate",
            "mediafile",
            "projector",
            "projection",
            "projector_message",
            "projector_countdown",
            "chat_group",
            "chat_message",
        ):
            assert data[collection] == {}

        assert data["_migration_index"]

    def test_no_permissions(self) -> None:
        self.set_models(
            {
                "meeting/1": {"name": "test_foo"},
                "user/1": {
                    "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
                },
            }
        )
        status_code, data = self.request("export_meeting", {"meeting_id": 1})
        assert status_code == 403

    def test_with_locked_meeting(self) -> None:
        self.set_models(
            {
                "meeting/1": {"name": "test_foo", "locked_from_inside": True},
            }
        )
        status_code, data = self.request("export_meeting", {"meeting_id": 1})
        assert status_code == 400
        assert data["message"] == "Cannot export: meeting 1 is locked."

    def test_organization_tags_exclusion(self) -> None:
        self.set_models(
            {
                "meeting/1": {"name": "name_foo", "organization_tag_ids": [12]},
                "organization_tag/12": {
                    "name": "name_bar",
                    "tagged_ids": ["meeting/1"],
                },
            }
        )
        status_code, data = self.request("export_meeting", {"meeting_id": 1})
        assert status_code == 200
        assert "organization_tag" not in data
        assert data["meeting"]["1"].get("organization_tag_ids") is None

    def test_action_worker_import_preview_exclusion(self) -> None:
        self.set_models(
            {
                "meeting/1": {"name": "name_foo"},
                "action_worker/1": {
                    "id": 1,
                    "name": "testcase",
                    "state": ActionWorkerState.END,
                    "created": round(time() - 3),
                    "timestamp": round(time()),
                },
                "import_preview/1": {
                    "id": 1,
                    "name": "topic",
                    "state": "done",
                    "created": round(time()),
                },
            }
        )
        status_code, data = self.request("export_meeting", {"meeting_id": 1})
        assert status_code == 200
        assert "action_worker" not in data
        assert "import_preview" not in data

    def test_add_users(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "name": "exported_meeting",
                    "user_ids": [1],
                    "group_ids": [11],
                    "present_user_ids": [1],
                    "meeting_user_ids": [1],
                },
                "gender/1": {"name": "male"},
                "user/1": {
                    "is_present_in_meeting_ids": [1],
                    "meeting_user_ids": [1],
                    "gender_id": 1,
                },
                "meeting_user/1": {
                    "meeting_id": 1,
                    "user_id": 1,
                    "group_ids": [11],
                },
                "group/11": {
                    "name": "group_in_meeting_1",
                    "meeting_id": 1,
                    "meeting_user_ids": [1],
                },
            }
        )
        status_code, data = self.request("export_meeting", {"meeting_id": 1})
        assert status_code == 200
        assert data["user"]["1"]["organization_management_level"] == "superadmin"
        assert data["user"]["1"]["username"] == "admin"
        assert data["user"]["1"]["is_active"] is True
        assert data["user"]["1"]["meeting_ids"] == [1]
        assert data["user"]["1"]["is_present_in_meeting_ids"] == [1]
        assert data["user"]["1"]["gender"] == "male"
        assert data["meeting_user"]["1"]["group_ids"] == [11]

    def test_add_users_in_2_meetings(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "name": "exported_meeting",
                    "user_ids": [1],
                    "group_ids": [11],
                    "present_user_ids": [1],
                    "meeting_user_ids": [1, 2],
                },
                "meeting/2": {
                    "name": "not exported_meeting",
                    "user_ids": [1],
                    "group_ids": [12],
                    "present_user_ids": [1],
                },
                "user/1": {
                    "is_present_in_meeting_ids": [1, 2],
                    "meeting_ids": [1, 2],
                    "meeting_user_ids": [1, 2],
                },
                "meeting_user/1": {
                    "meeting_id": 1,
                    "user_id": 1,
                    "group_ids": [11],
                },
                "meeting_user/2": {
                    "meeting_id": 2,
                    "user_id": 1,
                    "group_ids": [12],
                },
                "group/11": {
                    "name": "group_in_meeting_1",
                    "meeting_id": 1,
                    "meeting_user_ids": [1],
                },
                "group/12": {
                    "name": "group_in_meeting_2",
                    "meeting_id": 2,
                    "meeting_user_ids": [2],
                },
            }
        )
        status_code, data = self.request("export_meeting", {"meeting_id": 1})
        assert status_code == 200
        assert data["user"]["1"]["organization_management_level"] == "superadmin"
        assert data["user"]["1"]["username"] == "admin"
        assert data["user"]["1"]["is_active"] is True
        assert data["user"]["1"]["meeting_ids"] == [1]
        assert data["user"]["1"]["is_present_in_meeting_ids"] == [1]
        assert data["meeting_user"]["1"]["group_ids"] == [11]

    def test_export_meeting_with_ex_user(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "name": "exported_meeting",
                    "motion_submitter_ids": [1],
                    "motion_ids": [1],
                    "list_of_speakers_ids": [1],
                    "personal_note_ids": [34],
                    "meeting_user_ids": [11, 12],
                },
                "user/11": {
                    "username": "exuser11",
                    "meeting_user_ids": [11],
                },
                "user/12": {
                    "username": "exuser12",
                    "meeting_user_ids": [12],
                },
                "meeting_user/11": {
                    "meeting_id": 1,
                    "user_id": 11,
                    "motion_submitter_ids": [1],
                },
                "meeting_user/12": {
                    "meeting_id": 1,
                    "user_id": 12,
                    "personal_note_ids": [34],
                },
                "motion/1": {
                    "list_of_speakers_id": 1,
                    "meeting_id": 1,
                    "sequential_number": 1,
                    "state_id": 1,
                    "submitter_ids": [1],
                    "title": "dummy",
                },
                "motion_submitter/1": {
                    "meeting_user_id": 11,
                    "motion_id": 1,
                    "meeting_id": 1,
                },
                "list_of_speakers/1": {
                    "content_object_id": "motion/1",
                    "meeting_id": 1,
                    "sequential_number": 1,
                },
                "motion_state/1": {
                    "motion_ids": [1],
                },
                "personal_note/34": {
                    "meeting_user_id": 12,
                    "meeting_id": 1,
                    "note": "note_in_meeting1",
                },
            }
        )
        status_code, data = self.request("export_meeting", {"meeting_id": 1})
        assert status_code == 200
        assert data["meeting"]["1"].get("user_ids") is None
        user11 = data["user"]["11"]
        assert user11.get("username") == "exuser11"
        assert user11.get("meeting_user_ids") == [11]
        self.assert_model_exists("meeting_user/11", {"motion_submitter_ids": [1]})
        user12 = data["user"]["12"]
        assert user12.get("username") == "exuser12"
        meeting_user_12 = data["meeting_user"]["12"]
        assert meeting_user_12.get("meeting_id") == 1
        assert meeting_user_12.get("user_id") == 12
        assert meeting_user_12.get("personal_note_ids") == [34]

    def test_export_meeting_find_special_users(self) -> None:
        """Find users in:
        Collection          | Field
        meeting             | present_user_ids

        Find meeting_users in:
        Collection          | Field
        poll                | voted_ids
        motion              | supporter_meeting_user_ids
        ballot              | acting_meeting_user_id
        ballot              | represented_meeting_user_id
        poll_config_option  | meeting_user_id
        """
        self.create_meeting()
        self.create_motion(1, 30)
        self.set_models(
            {
                "meeting/1": {"present_user_ids": [11]},
                "user/11": {"username": "exuser11"},
                "user/12": {"username": "exuser12"},
                "user/13": {"username": "exuser13"},
                "user/14": {"username": "exuser14"},
                "assignment/10": {"title": "test", "meeting_id": 1},
                "list_of_speakers/11": {
                    "content_object_id": "assignment/10",
                    "meeting_id": 1,
                },
                "motion/30": {
                    "meeting_id": 1,
                    "supporter_meeting_user_ids": [112],
                },
                "poll/80": {
                    "title": "Poll 80",
                    "meeting_id": 1,
                    "content_object_id": "assignment/10",
                    "visibility": Poll.VISIBILITY_NAMED,
                    "config_id": "poll_config_approval/90",
                    "state": Poll.STATE_STARTED,
                    "voted_ids": [114],
                },
                "poll_config_approval/90": {"poll_id": 80},
                "poll_config_option/100": {
                    "poll_config_id": "poll_config_approval/90",
                    "meeting_user_id": 113,
                },
                "ballot/120": {
                    "poll_id": 80,
                    "value": "yes",
                    "represented_meeting_user_id": 114,
                    "acting_meeting_user_id": 114,
                },
                "meeting_user/112": {
                    "meeting_id": 1,
                    "user_id": 12,
                    "group_ids": [1],
                },
                "meeting_user/113": {
                    "meeting_id": 1,
                    "user_id": 13,
                    "group_ids": [1],
                },
                "meeting_user/114": {
                    "meeting_id": 1,
                    "user_id": 14,
                    "group_ids": [1],
                },
            }
        )
        status_code, data = self.request("export_meeting", {"meeting_id": 1})
        assert status_code == 200
        assert data["meeting"]["1"].get("user_ids") is None
        for id_ in range(11, 15):
            assert data["user"][str(id_)]
        for id_ in range(112, 115):
            assert data["meeting_user"][str(id_)]

        assert data["meeting"]["1"]["present_user_ids"] == [11]
        assert data["user"]["11"]["is_present_in_meeting_ids"] == [1]

        assert data["motion"]["30"]["supporter_meeting_user_ids"] == [112]
        assert data["meeting_user"]["112"]["supported_motion_ids"] == [30]

        assert data["poll_config_option"]["100"]["meeting_user_id"] == 113
        assert data["meeting_user"]["113"]["poll_option_ids"] == [100]

        assert data["poll"]["80"]["voted_ids"] == [114]
        assert data["meeting_user"]["114"]["poll_voted_ids"] == [80]
        assert data["ballot"]["120"]["c"] == 114
        assert data["ballot"]["120"]["represented_meeting_user_id"] == 114
        assert data["meeting_user"]["114"]["acting_ballot_ids"] == [120]
        assert data["meeting_user"]["114"]["represented_ballot_ids"] == [120]
