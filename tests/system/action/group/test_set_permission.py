from tests.system.action.base import BaseActionTestCase


class GroupSetPermissionActionTest(BaseActionTestCase):
    def test_set_permission_set_true(self) -> None:
        self.create_model(
            "group/11",
            {
                "name": "group_11",
                "permissions": ["agenda_item.can_manage", "motion.can_create"],
            },
        )
        response = self.request(
            "group.set_permission",
            {"id": 11, "permission": "projector.can_see", "set": True},
        )
        self.assert_status_code(response, 200)
        model = self.get_model("group/11")
        assert model.get("permissions") == [
            "agenda_item.can_manage",
            "motion.can_create",
            "projector.can_see",
        ]

    def test_set_permission_reset(self) -> None:
        self.create_model(
            "group/11",
            {
                "name": "group_11",
                "permissions": ["agenda_item.can_manage", "motion.can_create"],
            },
        )
        response = self.request(
            "group.set_permission",
            {"id": 11, "permission": "agenda_item.can_manage", "set": True},
        )
        self.assert_status_code(response, 200)
        model = self.get_model("group/11")
        assert model.get("permissions") == [
            "agenda_item.can_manage",
            "motion.can_create",
        ]

    def test_set_permission_set_false(self) -> None:
        self.create_model(
            "group/11",
            {
                "name": "group_11",
                "permissions": ["agenda_item.can_manage", "motion.can_create"],
            },
        )
        response = self.request(
            "group.set_permission",
            {"id": 11, "permission": "agenda_item.can_manage", "set": False},
        )
        self.assert_status_code(response, 200)
        model = self.get_model("group/11")
        assert model.get("permissions") == ["motion.can_create"]

    def test_set_permission_reunset(self) -> None:
        self.create_model(
            "group/11", {"name": "group_11", "permissions": ["agenda_item.can_manage"]}
        )
        response = self.request(
            "group.set_permission",
            {"id": 11, "permission": "motion.can_create", "set": False},
        )
        self.assert_status_code(response, 200)
        model = self.get_model("group/11")
        assert model.get("permissions") == ["agenda_item.can_manage"]
