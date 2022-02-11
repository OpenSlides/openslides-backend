from openslides_backend.models.fields import BaseRelationField, BaseTemplateField
from openslides_backend.models.models import User
from openslides_backend.shared.patterns import Collection
from tests.system.action.base import BaseActionTestCase


class MeetingDeleteActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.set_models(
            {
                "organization/1": {
                    "committee_ids": [1],
                    "active_meeting_ids": [1],
                },
                "committee/1": {
                    "organization_id": 1,
                    "name": "test_committee",
                    "meeting_ids": [1],
                },
                "group/11": {
                    "meeting_id": 1,
                },
                "user/1": {
                    "username": "user1",
                },
                "user/2": {},
                "meeting/1": {
                    "name": "test",
                    "committee_id": 1,
                    "is_active_in_organization_id": 1,
                    "group_ids": [11],
                },
            }
        )

    def test_delete_no_permissions(self) -> None:
        self.set_models(
            {"user/1": {"organization_management_level": "can_manage_users"}}
        )
        response = self.request("meeting.delete", {"id": 1})
        self.assert_status_code(response, 403)
        assert (
            "Missing CommitteeManagementLevel: can_manage" in response.json["message"]
        )

    def test_delete_permissions_can_manage_organization(self) -> None:
        self.set_models(
            {"user/1": {"organization_management_level": "can_manage_organization"}}
        )
        response = self.request("meeting.delete", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("meeting/1")

    def test_delete_permissions_can_manage_committee(self) -> None:
        self.set_models(
            {
                "user/1": {
                    "committee_$can_manage_management_level": [1],
                    "committee_$_management_level": ["can_manage"],
                    "organization_management_level": "can_manage_users",
                }
            }
        )
        response = self.request("meeting.delete", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("meeting/1")

    def test_delete_full_meeting(self) -> None:
        self.load_example_data()
        self.set_models(
            {
                "meeting/1": {"all_projection_ids": [1, 2, 3, 4, 5]},
                "projection/5": {
                    "current_projector_id": None,
                    "preview_projector_id": None,
                    "history_projector_id": 1,
                    "content_object_id": "assignment/1",
                    "stable": False,
                    "type": None,
                    "weight": 1,
                    "options": {},
                    "meeting_id": 1,
                },
            }
        )
        response = self.request("meeting.delete", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_deleted(
            "meeting/1", {"committee_id": 1, "group_ids": [1, 2, 3, 4, 5]}
        )
        self.assert_model_exists("committee/1", {"meeting_ids": []})
        # assert all related models are deleted
        for i in range(5):
            self.assert_model_deleted(f"group/{i+1}", {"meeting_id": 1})
        self.assert_model_deleted("personal_note/1")
        for i in range(3):
            self.assert_model_deleted(f"tag/{i+1}")
        for i in range(15):
            self.assert_model_deleted(f"agenda_item/{i+1}")
        for i in range(16):
            self.assert_model_deleted(f"list_of_speakers/{i+1}")
        for i in range(13):
            self.assert_model_deleted(f"speaker/{i+1}")
        for i in range(8):
            self.assert_model_deleted(f"topic/{i+1}")
        for i in range(4):
            self.assert_model_deleted(f"motion/{i+1}")
        for i in range(4):
            self.assert_model_deleted(f"motion_submitter/{i+1}")
        self.assert_model_deleted("motion_comment/1")
        self.assert_model_deleted("motion_comment_section/1")
        for i in range(2):
            self.assert_model_deleted(f"motion_category/{i+1}")
        self.assert_model_deleted("motion_block/1")
        for i in range(2):
            self.assert_model_deleted(f"motion_change_recommendation/{i+4}")
        for i in range(14):
            self.assert_model_deleted(f"motion_state/{i+1}")
        for i in range(2):
            self.assert_model_deleted(f"motion_workflow/{i+1}")
        for i in range(5):
            self.assert_model_deleted(f"poll/{i+1}")
        for i in range(13):
            self.assert_model_deleted(f"option/{i+1}")
        for i in range(9):
            self.assert_model_deleted(f"vote/{i+1}")
        for i in range(2):
            self.assert_model_deleted(f"assignment/{i+1}")
        for i in range(5):
            self.assert_model_deleted(f"assignment_candidate/{i+1}")
        for i in range(1):
            self.assert_model_deleted(f"mediafile/{i+1}")
        for i in range(2):
            self.assert_model_deleted(f"projector/{i+1}")
        for i in range(5):
            self.assert_model_deleted(f"projection/{i+1}")
        self.assert_model_deleted("projector_message/1")
        for i in range(2):
            self.assert_model_deleted(f"projector_countdown/{i+1}")
        for i in range(2):
            self.assert_model_deleted(f"chat_group/{i+1}")
        # assert that all structured fields on all users of the meeting are deleted.
        for i in range(3):
            user = self.get_model(f"user/{i+1}")
            for field in User().get_fields():
                if isinstance(
                    field, BaseTemplateField
                ) and field.replacement_collection == Collection("meeting"):
                    assert user[field.get_template_field_name()] == []
                    val = user.get(field.get_structured_field_name(1))
                    if isinstance(field, BaseRelationField) and field.is_list_field:
                        assert val in ([], None)
                    else:
                        assert val is None

    def test_delete_with_tag_and_motion(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "tag_ids": [42],
                    "motion_ids": [1],
                },
                "tag/42": {"meeting_id": 1, "tagged_ids": ["motion/1"]},
                "motion/1": {"meeting_id": 1, "tag_ids": [42]},
            }
        )
        response = self.request("meeting.delete", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists("committee/1", {"meeting_ids": []})
        self.assert_model_deleted("meeting/1", {"committee_id": 1, "tag_ids": [42]})
        self.assert_model_deleted(
            "tag/42", {"meeting_id": 1, "tagged_ids": ["motion/1"]}
        )
        self.assert_model_deleted("motion/1", {"meeting_id": 1, "tag_ids": [42]})

    def test_delete_with_history_projection(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "all_projection_ids": [42],
                    "projector_ids": [1],
                    "is_active_in_organization_id": 1,
                },
                "projector/1": {
                    "meeting_id": 1,
                    "history_projection_ids": [42],
                    "current_projection_ids": [42],
                },
                "projection/42": {
                    "meeting_id": 1,
                    "content_object_id": "meeting/1",
                    "history_projector_id": 1,
                    "current_projector_id": 1,
                    "stable": False,
                },
            }
        )
        response = self.request("meeting.delete", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists("committee/1", {"meeting_ids": []})
        self.assert_model_deleted(
            "meeting/1",
            {"committee_id": 1, "all_projection_ids": [42], "projector_ids": [1]},
        )
        self.assert_model_deleted(
            "projector/1", {"meeting_id": 1, "history_projection_ids": [42]}
        )
        self.assert_model_deleted(
            "projection/42",
            {
                "meeting_id": 1,
                "content_object_id": "meeting/1",
                "history_projector_id": 1,
                "stable": False,
            },
        )

    def test_delete_meeting_with_relations(self) -> None:
        self.set_models(
            {
                "committee/1": {
                    "user_ids": [1, 2],
                    "user_$can_manage_management_level": [1],
                    "user_$_management_level": ["can_manage"],
                },
                "user/1": {
                    "committee_$can_manage_management_level": [1],
                    "committee_$_management_level": ["can_manage"],
                    "organization_management_level": "can_manage_users",
                    "committee_ids": [1],
                },
                "user/2": {
                    "group_$_ids": ["1"],
                    "group_$1_ids": [11],
                    "committee_ids": [1],
                },
                "group/11": {
                    "user_ids": [2],
                },
                "meeting/1": {
                    "user_ids": [2],
                },
            }
        )
        response = self.request("meeting.delete", {"id": 1})
        self.assert_status_code(response, 200)
        meeting1 = self.assert_model_deleted(
            "meeting/1",
            {"group_ids": [11], "committee_id": 1, "is_active_in_organization_id": 1},
        )
        # One would expect the user_ids is still filled with user_ids = [2],
        # but relation user_ids will be reseted in an execute_other_action
        # group.delete without context of meeting.delete
        self.assertCountEqual(meeting1.get("user_ids", []), [])

        self.assert_model_exists(
            "organization/1", {"active_meeting_ids": [], "committee_ids": [1]}
        )
        self.assert_model_exists(
            "committee/1",
            {
                "user_ids": [1],
                "meeting_ids": [],
                "user_$can_manage_management_level": [1],
                "user_$_management_level": ["can_manage"],
            },
        )
        self.assert_model_deleted("group/11", {"user_ids": [2], "meeting_id": 1})
        self.assert_model_exists(
            "user/1",
            {
                "committee_ids": [1],
                "committee_$_management_level": ["can_manage"],
                "committee_$can_manage_management_level": [1],
            },
        )
        self.assert_model_exists("user/2", {"group_$_ids": [], "committee_ids": []})

    def test_delete_archived_meeting(self) -> None:
        self.set_models(
            {
                "organization/1": {"active_meeting_ids": []},
                "committee/1": {
                    "user_ids": [1, 2],
                    "user_$can_manage_management_level": [1],
                    "user_$_management_level": ["can_manage"],
                },
                "user/1": {
                    "committee_$can_manage_management_level": [1],
                    "committee_$_management_level": ["can_manage"],
                    "organization_management_level": "can_manage_users",
                    "committee_ids": [1],
                },
                "user/2": {
                    "group_$_ids": ["1"],
                    "group_$1_ids": [11],
                    "committee_ids": [1],
                },
                "group/11": {
                    "user_ids": [2],
                },
                "meeting/1": {
                    "user_ids": [2],
                    "is_active_in_organization_id": None,
                },
            }
        )
        response = self.request("meeting.delete", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("meeting/1")
