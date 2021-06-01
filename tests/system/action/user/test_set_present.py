from tests.system.action.base import BaseActionTestCase


class UserSetPresentActionTest(BaseActionTestCase):
    def test_set_present_add_correct(self) -> None:
        self.set_models(
            {"meeting/1": {}, "user/111": {"username": "username_srtgb123"}}
        )
        response = self.request(
            "user.set_present", {"id": 111, "meeting_id": 1, "present": True}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("user/111")
        assert model.get("is_present_in_meeting_ids") == [1]
        meeting = self.get_model("meeting/1")
        assert meeting.get("present_user_ids") == [111]

    def test_set_present_del_correct(self) -> None:
        self.set_models(
            {
                "meeting/1": {"present_user_ids": [111]},
                "user/111": {
                    "username": "username_srtgb123",
                    "is_present_in_meeting_ids": [1],
                },
            }
        )
        response = self.request(
            "user.set_present", {"id": 111, "meeting_id": 1, "present": False}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("user/111")
        assert model.get("is_present_in_meeting_ids") == []
        meeting = self.get_model("meeting/1")
        assert meeting.get("present_user_ids") == []

    def test_set_present_null_action(self) -> None:
        self.set_models(
            {
                "meeting/1": {"present_user_ids": []},
                "user/111": {
                    "username": "username_srtgb123",
                    "is_present_in_meeting_ids": [],
                },
            }
        )
        response = self.request(
            "user.set_present", {"id": 111, "meeting_id": 1, "present": False}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("user/111")
        assert model.get("is_present_in_meeting_ids") == []
        meeting = self.get_model("meeting/1")
        assert meeting.get("present_user_ids") == []

    def test_set_present_add_self_correct(self) -> None:
        self.create_model("meeting/1", {"users_allow_self_set_present": True})
        response = self.request(
            "user.set_present", {"id": 1, "meeting_id": 1, "present": True}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("user/1")
        assert model.get("is_present_in_meeting_ids") == [1]
        meeting = self.get_model("meeting/1")
        assert meeting.get("present_user_ids") == [1]

    def test_set_present_no_permissions(self) -> None:
        self.set_models(
            {
                "meeting/1": {"users_allow_self_set_present": False},
                "user/1": {"organisation_management_level": None},
            }
        )
        response = self.request(
            "user.set_present", {"id": 1, "meeting_id": 1, "present": True}
        )
        self.assert_status_code(response, 403)

    def test_set_present_orga_can_manage_permission(self) -> None:
        self.set_models(
            {
                "meeting/1": {"users_allow_self_set_present": False},
                "user/1": {"organisation_management_level": "can_manage_users"},
            }
        )
        response = self.request(
            "user.set_present", {"id": 1, "meeting_id": 1, "present": True}
        )
        self.assert_status_code(response, 200)

    def test_set_present_committee_can_manage_permission(self) -> None:
        self.set_models(
            {
                "meeting/1": {"users_allow_self_set_present": False, "committee_id": 1},
                "committee/1": {"user_ids": [1]},
                "user/1": {
                    "organisation_management_level": None,
                    "committee_ids": [1],
                    "committee_$1_management_level": "can_manage",
                },
            }
        )
        response = self.request(
            "user.set_present", {"id": 1, "meeting_id": 1, "present": True}
        )
        self.assert_status_code(response, 200)

    def test_set_present_meeting_can_manage_permission(self) -> None:
        self.set_models(
            {
                "meeting/1": {"users_allow_self_set_present": False, "group_ids": [1]},
                "group/1": {"user_ids": [1], "permissions": ["user.can_manage"]},
                "user/1": {
                    "organisation_management_level": None,
                    "group_$1_ids": [1],
                },
            }
        )
        response = self.request(
            "user.set_present", {"id": 1, "meeting_id": 1, "present": True}
        )
        self.assert_status_code(response, 200)

    def test_set_present_self_permission(self) -> None:
        self.set_models(
            {
                "meeting/1": {"users_allow_self_set_present": True},
                "user/1": {"organisation_management_level": None},
            }
        )
        response = self.request(
            "user.set_present", {"id": 1, "meeting_id": 1, "present": True}
        )
        self.assert_status_code(response, 200)
