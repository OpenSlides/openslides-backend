from openslides_backend.models.fields import BaseRelationField, BaseTemplateField
from openslides_backend.models.models import User
from openslides_backend.shared.patterns import Collection
from tests.system.action.base import BaseActionTestCase


class MeetingDeleteActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.set_models(
            {
                "user/1": {"organization_management_level": "can_manage_users"},
                "committee/1": {"name": "test_committee", "user_ids": [1, 2]},
                "group/1": {},
                "user/2": {},
                "meeting/1": {"name": "test", "committee_id": 1},
            }
        )

    def test_delete_no_permissions(self) -> None:
        response = self.request("meeting.delete", {"id": 1})
        self.assert_status_code(response, 403)
        assert (
            "Missing CommitteeManagementLevel: can_manage" in response.json["message"]
        )

    def test_delete_permissions(self) -> None:
        self.set_models({"user/1": {"committee_$1_management_level": "can_manage"}})
        response = self.request("meeting.delete", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("meeting/1")

    def test_delete_full_meeting(self) -> None:
        self.load_example_data()
        response = self.request("meeting.delete", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("meeting/1")
        self.assert_model_exists("committee/1", {"meeting_ids": []})
        # assert all related models are deleted
        for i in range(5):
            self.assert_model_deleted(f"group/{i+1}")
        self.assert_model_deleted("personal_note/1")
        for i in range(3):
            self.assert_model_deleted(f"tag/{i+1}")
        for i in range(15):
            self.assert_model_deleted(f"agenda_item/{i+1}")
        for i in range(18):
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
        for i in range(3):
            self.assert_model_deleted(f"mediafile/{i+1}")
        for i in range(2):
            self.assert_model_deleted(f"projector/{i+1}")
        for i in range(4):
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
