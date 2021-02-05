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

    def test_set_present_add_self_not_allowed(self) -> None:
        self.create_model("meeting/1", {"users_allow_self_set_present": False})
        response = self.request(
            "user.set_present", {"id": 1, "meeting_id": 1, "present": True}
        )
        self.assert_status_code(response, 400)
        assert (
            "Users are not allowed to set present self in this meeting."
            in response.json["message"]
        )
