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
            "meeting_id": 1,
        },
        "list_of_speakers/42": {
            "content_object_id": "topic/2",
            "meeting_id": 1,
        },
        "topic/1": {"meeting_id": 1, "title": "tropic"},
        "topic/2": {"meeting_id": 1, "title": "tropic"},
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
                    "meeting_id": 222,
                },
                "list_of_speakers/42": {
                    "content_object_id": "topic/2",
                    "meeting_id": 222,
                },
                "list_of_speakers/64": {
                    "content_object_id": "topic/3",
                    "meeting_id": 222,
                },
                "topic/1": {
                    "meeting_id": 222,
                    "title": "tropic",
                },
                "topic/2": {
                    "meeting_id": 222,
                    "title": "tropic",
                },
                "topic/3": {
                    "meeting_id": 222,
                    "title": "tropic",
                },
            }
        )
        response = self.request(
            "agenda_item.assign", {"meeting_id": 222, "ids": [8, 9], "parent_id": None}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "agenda_item/7",
            {
                "child_ids": [],
                "parent_id": None,
            },
        )
        self.assert_model_exists(
            "agenda_item/8",
            {
                "child_ids": [],
                "parent_id": None,
                "level": 0,
                "weight": 10000,
            },
        )
        self.assert_model_exists(
            "agenda_item/9",
            {
                "child_ids": [],
                "parent_id": None,
                "level": 0,
                "weight": 10001,
            },
        )

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
                    "meeting_id": 222,
                },
                "list_of_speakers/42": {
                    "content_object_id": "topic/2",
                    "meeting_id": 222,
                },
                "list_of_speakers/64": {
                    "content_object_id": "topic/3",
                    "meeting_id": 222,
                },
                "topic/1": {
                    "meeting_id": 222,
                    "title": "tropic",
                },
                "topic/2": {
                    "meeting_id": 222,
                    "title": "tropic",
                },
                "topic/3": {
                    "meeting_id": 222,
                    "title": "tropic",
                },
            }
        )
        with CountDatastoreCalls() as counter:
            response = self.request(
                "agenda_item.assign", {"meeting_id": 222, "ids": [8, 9], "parent_id": 7}
            )
        self.assert_status_code(response, 200)
        assert counter.calls == 11
        self.assert_model_exists(
            "agenda_item/7",
            {
                "child_ids": [8, 9],
                "parent_id": None,
            },
        )
        self.assert_model_exists(
            "agenda_item/8",
            {
                "child_ids": [],
                "parent_id": 7,
                "level": 1,
                "weight": 101,
            },
        )
        self.assert_model_exists(
            "agenda_item/9",
            {
                "child_ids": [],
                "parent_id": 7,
                "level": 1,
                "weight": 102,
            },
        )

    def test_assign_multiple_action_data_items(self) -> None:
        self.create_meeting(222)
        self.set_models(
            {
                "agenda_item/7": {"meeting_id": 222, "content_object_id": "topic/1"},
                "agenda_item/8": {"meeting_id": 222, "content_object_id": "topic/2"},
                "list_of_speakers/23": {
                    "content_object_id": "topic/1",
                    "meeting_id": 222,
                },
                "list_of_speakers/42": {
                    "content_object_id": "topic/2",
                    "meeting_id": 222,
                },
                "topic/1": {
                    "meeting_id": 222,
                    "title": "tropic",
                },
                "topic/2": {
                    "meeting_id": 222,
                    "title": "tropic",
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
        self.assert_model_exists("agenda_item/7", {"parent_id": None})
        self.assert_model_exists("agenda_item/8", {"parent_id": None})

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
