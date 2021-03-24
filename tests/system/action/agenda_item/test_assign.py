from tests.system.action.base import BaseActionTestCase


class AgendaItemAssignActionTest(BaseActionTestCase):
    def test_assign_parent_none(self) -> None:
        self.set_models(
            {
                "meeting/222": {"name": "name_SNLGsvIV"},
                "agenda_item/7": {
                    "comment": "comment_7",
                    "meeting_id": 222,
                    "parent_id": None,
                    "child_ids": [8, 9],
                },
                "agenda_item/8": {
                    "comment": "comment_8",
                    "meeting_id": 222,
                    "parent_id": 7,
                    "child_ids": [],
                },
                "agenda_item/9": {
                    "comment": "comment_9",
                    "meeting_id": 222,
                    "parent_id": 7,
                    "child_ids": [],
                },
            }
        )
        response = self.request(
            "agenda_item.assign", {"meeting_id": 222, "ids": [8, 9], "parent_id": None}
        )
        self.assert_status_code(response, 200)
        agenda_item_7 = self.get_model("agenda_item/7")
        assert agenda_item_7.get("child_ids") == []
        assert agenda_item_7.get("parent_id") is None
        agenda_item_8 = self.get_model("agenda_item/8")
        assert agenda_item_8.get("child_ids") == []
        assert agenda_item_8.get("parent_id") is None
        agenda_item_9 = self.get_model("agenda_item/9")
        assert agenda_item_9.get("child_ids") == []
        assert agenda_item_9.get("parent_id") is None

    def test_assign_parent_set(self) -> None:
        self.set_models(
            {
                "meeting/222": {"name": "name_SNLGsvIV"},
                "agenda_item/7": {
                    "comment": "comment_7",
                    "meeting_id": 222,
                    "parent_id": None,
                    "child_ids": [],
                },
                "agenda_item/8": {
                    "comment": "comment_8",
                    "meeting_id": 222,
                    "parent_id": None,
                    "child_ids": [],
                },
                "agenda_item/9": {
                    "comment": "comment_9",
                    "meeting_id": 222,
                    "parent_id": None,
                    "child_ids": [],
                },
            }
        )
        response = self.request(
            "agenda_item.assign", {"meeting_id": 222, "ids": [8, 9], "parent_id": 7}
        )
        self.assert_status_code(response, 200)
        agenda_item_7 = self.get_model("agenda_item/7")
        assert agenda_item_7.get("child_ids") == [8, 9]
        assert agenda_item_7.get("parent_id") is None
        agenda_item_8 = self.get_model("agenda_item/8")
        assert agenda_item_8.get("child_ids") == []
        assert agenda_item_8.get("parent_id") == 7
        agenda_item_9 = self.get_model("agenda_item/9")
        assert agenda_item_9.get("child_ids") == []
        assert agenda_item_9.get("parent_id") == 7

    def test_assign_multiple_action_data_items(self) -> None:
        self.set_models(
            {
                "meeting/222": {},
                "agenda_item/7": {"meeting_id": 222},
                "agenda_item/8": {"meeting_id": 222},
            }
        )
        response = self.request_multi(
            "agenda_item.assign",
            [
                {"meeting_id": 222, "ids": [8], "parent_id": 7},
                {"meeting_id": 222, "ids": [7], "parent_id": 8},
            ],
        )
        self.assert_status_code(response, 400)
        agenda_item_7 = self.get_model("agenda_item/7")
        assert agenda_item_7.get("parent_id") is None
        agenda_item_8 = self.get_model("agenda_item/8")
        assert agenda_item_8.get("parent_id") is None

    def test_permissions(self) -> None:
        self.base_permission_test(
            {
                "meeting/222": {},
                "agenda_item/7": {"meeting_id": 222},
                "agenda_item/8": {"meeting_id": 222},
            },
            "agenda_item.assign",
            {"meeting_id": 222, "ids": [8], "parent_id": 7},
        )
