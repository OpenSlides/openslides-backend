from tests.system.action.base import BaseActionTestCase


class UserDeleteActionTest(BaseActionTestCase):
    def test_delete_correct(self) -> None:
        self.create_model("user/111", {"username": "username_srtgb123"})
        response = self.client.post(
            "/",
            json=[{"action": "user.delete", "data": [{"id": 111}]}],
        )

        self.assert_status_code(response, 200)
        self.assert_model_deleted("user/111")

    def test_delete_wrong_id(self) -> None:
        self.create_model("user/112", {"username": "username_srtgb123"})
        response = self.client.post(
            "/",
            json=[{"action": "user.delete", "data": [{"id": 111}]}],
        )
        self.assert_status_code(response, 400)
        model = self.get_model("user/112")
        assert model.get("username") == "username_srtgb123"

    def test_delete_correct_with_template_field(self) -> None:
        self.create_model(
            "user/111",
            {
                "username": "username_srtgb123",
                "group_$_ids": ["42"],
                "group_$42_ids": [456],
            },
        )
        self.create_model("group/456", {"meeting_id": 42, "user_ids": [111, 222]})
        self.create_model("meeting/42", {"group_ids": [456], "user_ids": [111]})
        response = self.client.post(
            "/",
            json=[{"action": "user.delete", "data": [{"id": 111}]}],
        )

        self.assert_status_code(response, 200)
        self.assert_model_deleted("user/111")
        model = self.get_model("group/456")
        assert model.get("user_ids") == [222]
        # check meeting.user_ids
        meeting = self.get_model("meeting/42")
        assert meeting.get("user_ids") == []
