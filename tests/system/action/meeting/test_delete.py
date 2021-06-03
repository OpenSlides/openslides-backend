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
