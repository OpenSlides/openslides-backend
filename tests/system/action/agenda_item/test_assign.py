from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase
from tests.system.util import CountDatastoreCalls


class AgendaItemAssignActionTest(BaseActionTestCase):
    PERMISSION_TEST_MODELS = {
        "agenda_item/7": {"meeting_id": 1, "content_object_id": "topic/1"},
        "agenda_item/8": {"meeting_id": 1, "content_object_id": "topic/2"},
        "list_of_speakers/23": {
            "content_object_id": "topic/1",
            "sequential_number": 11,
            "meeting_id": 1,
        },
        "list_of_speakers/42": {
            "content_object_id": "topic/2",
            "sequential_number": 12,
            "meeting_id": 1,
        },
        "topic/1": {"meeting_id": 1, "title": "tropic", "sequential_number": 1},
        "topic/2": {"meeting_id": 1, "title": "tropic", "sequential_number": 2},
    }

    def test_assign_parent_none(self) -> None:
        self.create_meeting(222)
        self.set_models(
            {
                "agenda_item/7": {
                    "comment": "comment_7",
                    "meeting_id": 222,
                    "parent_id": None,
                    "child_ids": [8, 9],
                    "level": 0,
                    "weight": 100,
                    "content_object_id": "topic/1",
                },
                "agenda_item/8": {
                    "comment": "comment_8",
                    "meeting_id": 222,
                    "parent_id": 7,
                    "child_ids": [],
                    "content_object_id": "topic/2",
                },
                "agenda_item/9": {
                    "comment": "comment_9",
                    "meeting_id": 222,
                    "parent_id": 7,
                    "child_ids": [],
                    "content_object_id": "topic/3",
                },
                "list_of_speakers/23": {
                    "content_object_id": "topic/1",
                    "sequential_number": 11,
                    "meeting_id": 222,
                },
                "list_of_speakers/42": {
                    "content_object_id": "topic/2",
                    "sequential_number": 12,
                    "meeting_id": 222,
                },
                "list_of_speakers/64": {
                    "content_object_id": "topic/3",
                    "sequential_number": 13,
                    "meeting_id": 222,
                },
                "topic/1": {
                    "meeting_id": 222,
                    "title": "tropic",
                    "sequential_number": 1,
                },
                "topic/2": {
                    "meeting_id": 222,
                    "title": "tropic",
                    "sequential_number": 2,
                },
                "topic/3": {
                    "meeting_id": 222,
                    "title": "tropic",
                    "sequential_number": 3,
                },
            }
        )
        response = self.request(
            "agenda_item.assign", {"meeting_id": 222, "ids": [8, 9], "parent_id": None}
        )
        self.assert_status_code(response, 200)
        agenda_item_7 = self.get_model("agenda_item/7")
        assert agenda_item_7.get("child_ids") is None
        assert agenda_item_7.get("parent_id") is None
        agenda_item_8 = self.get_model("agenda_item/8")
        assert agenda_item_8.get("child_ids") is None
        assert agenda_item_8.get("parent_id") is None
        assert agenda_item_8.get("level") == 0
        assert agenda_item_8.get("weight") == 10000
        agenda_item_9 = self.get_model("agenda_item/9")
        assert agenda_item_9.get("child_ids") is None
        assert agenda_item_9.get("parent_id") is None
        assert agenda_item_9.get("level") == 0
        assert agenda_item_9.get("weight") == 10001

    def test_assign_parent_set(self) -> None:
        self.create_meeting(222)
        self.set_models(
            {
                "agenda_item/7": {
                    "comment": "comment_7",
                    "meeting_id": 222,
                    "parent_id": None,
                    "child_ids": [],
                    "level": 0,
                    "weight": 100,
                    "content_object_id": "topic/1",
                },
                "agenda_item/8": {
                    "comment": "comment_8",
                    "meeting_id": 222,
                    "parent_id": None,
                    "child_ids": [],
                    "content_object_id": "topic/2",
                },
                "agenda_item/9": {
                    "comment": "comment_9",
                    "meeting_id": 222,
                    "parent_id": None,
                    "child_ids": [],
                    "content_object_id": "topic/3",
                },
                "list_of_speakers/23": {
                    "content_object_id": "topic/1",
                    "sequential_number": 11,
                    "meeting_id": 222,
                },
                "list_of_speakers/42": {
                    "content_object_id": "topic/2",
                    "sequential_number": 12,
                    "meeting_id": 222,
                },
                "list_of_speakers/64": {
                    "content_object_id": "topic/3",
                    "sequential_number": 13,
                    "meeting_id": 222,
                },
                "topic/1": {
                    "meeting_id": 222,
                    "title": "tropic",
                    "sequential_number": 1,
                },
                "topic/2": {
                    "meeting_id": 222,
                    "title": "tropic",
                    "sequential_number": 2,
                },
                "topic/3": {
                    "meeting_id": 222,
                    "title": "tropic",
                    "sequential_number": 3,
                },
            }
        )
        with CountDatastoreCalls() as counter:
            response = self.request(
                "agenda_item.assign", {"meeting_id": 222, "ids": [8, 9], "parent_id": 7}
            )
        self.assert_status_code(response, 200)
        assert counter.calls == 15  # TODO this was 4 #befour
        agenda_item_7 = self.get_model("agenda_item/7")
        assert agenda_item_7.get("child_ids") == [8, 9]
        assert agenda_item_7.get("parent_id") is None
        agenda_item_8 = self.get_model("agenda_item/8")
        assert agenda_item_8.get("child_ids") is None
        assert agenda_item_8.get("parent_id") == 7
        assert agenda_item_8.get("level") == 1
        assert agenda_item_8.get("weight") == 101
        agenda_item_9 = self.get_model("agenda_item/9")
        assert agenda_item_9.get("child_ids") is None
        assert agenda_item_9.get("parent_id") == 7
        assert agenda_item_9.get("level") == 1
        assert agenda_item_9.get("weight") == 102

    def test_assign_multiple_action_data_items(self) -> None:
        self.create_meeting(222)
        self.set_models(
            {
                "agenda_item/7": {"meeting_id": 222, "content_object_id": "topic/1"},
                "agenda_item/8": {"meeting_id": 222, "content_object_id": "topic/2"},
                "list_of_speakers/23": {
                    "content_object_id": "topic/1",
                    "sequential_number": 11,
                    "meeting_id": 222,
                },
                "list_of_speakers/42": {
                    "content_object_id": "topic/2",
                    "sequential_number": 12,
                    "meeting_id": 222,
                },
                "topic/1": {
                    "meeting_id": 222,
                    "title": "tropic",
                    "sequential_number": 1,
                },
                "topic/2": {
                    "meeting_id": 222,
                    "title": "tropic",
                    "sequential_number": 2,
                },
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

    def test_assign_no_permissions(self) -> None:
        self.base_permission_test(
            self.PERMISSION_TEST_MODELS,
            "agenda_item.assign",
            {"meeting_id": 1, "ids": [8], "parent_id": 7},
        )

    def test_assign_permissions(self) -> None:
        self.base_permission_test(
            self.PERMISSION_TEST_MODELS,
            "agenda_item.assign",
            {"meeting_id": 1, "ids": [8], "parent_id": 7},
            Permissions.AgendaItem.CAN_MANAGE,
        )

    def test_assign_permissions_with_locked_meeting(self) -> None:
        self.base_permission_test(
            self.PERMISSION_TEST_MODELS,
            "agenda_item.assign",
            {"meeting_id": 1, "ids": [8], "parent_id": 7},
            OrganizationManagementLevel.SUPERADMIN,
            fail=True,
            lock_meeting=True,
        )

    def test_assign_permissions_with_locked_meeting_orgaadmin(self) -> None:
        self.base_permission_test(
            self.PERMISSION_TEST_MODELS,
            "agenda_item.assign",
            {"meeting_id": 1, "ids": [8], "parent_id": 7},
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
            fail=True,
            lock_meeting=True,
        )
