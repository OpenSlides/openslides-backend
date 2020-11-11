from tests.system.action.base import BaseActionTestCase


class GroupSetPermissionActionTest(BaseActionTestCase):
    def test_set_permission_set_true(self) -> None:
        self.create_model(
            "group/11", {"name": "group_11", "permissions": ["test", "bla"]}
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "group.set_permission",
                    "data": [{"id": 11, "permission": "top", "set": True}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("group/11")
        assert model.get("permissions") == ["test", "bla", "top"]

    def test_set_permission_reset(self) -> None:
        self.create_model(
            "group/11", {"name": "group_11", "permissions": ["test", "bla"]}
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "group.set_permission",
                    "data": [{"id": 11, "permission": "test", "set": True}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("group/11")
        assert model.get("permissions") == ["test", "bla"]

    def test_set_permission_set_false(self) -> None:
        self.create_model(
            "group/11", {"name": "group_11", "permissions": ["test", "bla"]}
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "group.set_permission",
                    "data": [{"id": 11, "permission": "test", "set": False}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("group/11")
        assert model.get("permissions") == ["bla"]

    def test_set_permission_reunset(self) -> None:
        self.create_model("group/11", {"name": "group_11", "permissions": ["test"]})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "group.set_permission",
                    "data": [{"id": 11, "permission": "bla", "set": False}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("group/11")
        assert model.get("permissions") == ["test"]
