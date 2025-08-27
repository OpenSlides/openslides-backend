from unittest.mock import Mock

from openslides_backend.action.action_handler import ActionHandler
from openslides_backend.action.util.typing import Payload
from openslides_backend.services.database.extended_database import ExtendedDatabase
from openslides_backend.services.postgresql.db_connection_handling import (
    get_new_os_conn,
)

from .base import BaseActionTestCase


class GeneralActionCommandFormat(BaseActionTestCase):
    # TODO later: either delete commented out code or implement locked fields
    """
    Tests the interface to datastore-command with one WriteRequest
    per payload-action and it's own locked_fields
    """

    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()

    def get_action_handler(self) -> ActionHandler:
        logger = Mock()
        config = Mock()
        handler = ActionHandler(config, self.services, logger)
        handler.user_id = 1
        handler.internal = False
        return handler

    def test_parse_actions_create_2_actions(self) -> None:
        payload: Payload = [
            {
                "action": "group.create",
                "data": [
                    {
                        "name": "group 1",
                        "meeting_id": 1,
                    }
                ],
            },
            {
                "action": "group.create",
                "data": [
                    {
                        "name": "group 2",
                        "meeting_id": 1,
                    }
                ],
            },
        ]

        action_handler = self.get_action_handler()
        with get_new_os_conn() as conn:
            ex_db = ExtendedDatabase(conn, action_handler.logging, action_handler.env)
            action_handler.datastore = ex_db
            write_requests, _ = action_handler.parse_actions(payload)
        self.assertEqual(len(write_requests), 2)
        self.assertEqual(len(write_requests[0].events), 2)
        # self.assertCountEqual(
        #     write_requests[0].locked_fields.keys(),
        #     [
        #         "group/weight",
        #         "meeting/1/group_ids",
        #     ],
        # )
        self.assertEqual(write_requests[0].events[0]["type"], "create")
        self.assertEqual(write_requests[0].events[1]["type"], "update")
        self.assertEqual(str(write_requests[0].events[0]["fqid"]), "group/4")
        self.assertEqual(str(write_requests[0].events[1]["fqid"]), "meeting/1")
        self.assertEqual(len(write_requests[1].events), 2)
        # self.assertCountEqual(
        #     write_requests[1].locked_fields.keys(),
        #     [
        #         "group/weight",
        #     ],
        # )

    def test_parse_actions_create_1_2_events(self) -> None:
        payload: Payload = [
            {
                "action": "group.create",
                "data": [
                    {
                        "name": "group 1",
                        "meeting_id": 1,
                    },
                    {
                        "name": "group 2",
                        "meeting_id": 1,
                    },
                ],
            },
        ]

        action_handler = self.get_action_handler()
        with get_new_os_conn() as conn:
            ex_db = ExtendedDatabase(conn, action_handler.logging, action_handler.env)
            action_handler.datastore = ex_db
            write_requests, _ = action_handler.parse_actions(payload)
        self.assertEqual(len(write_requests), 1)
        self.assertEqual(len(write_requests[0].events), 3)
        # self.assertCountEqual(
        #     write_requests[0].locked_fields.keys(),
        #     [
        #         "group/weight",
        #         "meeting/1/group_ids",
        #     ],
        # )
        self.assertEqual(write_requests[0].events[0]["type"], "create")
        self.assertEqual(write_requests[0].events[1]["type"], "create")
        self.assertEqual(write_requests[0].events[2]["type"], "update")
        self.assertEqual(str(write_requests[0].events[0]["fqid"]), "group/4")
        self.assertEqual(str(write_requests[0].events[1]["fqid"]), "group/5")
        self.assertEqual(str(write_requests[0].events[2]["fqid"]), "meeting/1")

    def test_create_2_actions(self) -> None:
        response = self.request_json(
            [
                {
                    "action": "group.create",
                    "data": [
                        {
                            "name": "group 1",
                            "meeting_id": 1,
                        }
                    ],
                },
                {
                    "action": "group.create",
                    "data": [
                        {
                            "name": "group 2",
                            "meeting_id": 1,
                        }
                    ],
                },
            ],
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("group/4", {"name": "group 1"})
        self.assert_model_exists("group/5", {"name": "group 2"})
        self.assert_model_exists("meeting/1", {"group_ids": [1, 2, 3, 4, 5]})

    def test_create_1_2_events(self) -> None:
        response = self.request_multi(
            "group.create",
            [
                {
                    "name": "group 1",
                    "meeting_id": 1,
                },
                {
                    "name": "group 2",
                    "meeting_id": 1,
                },
            ],
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("group/4", {"name": "group 1", "meeting_id": 1})
        self.assert_model_exists("group/5", {"name": "group 2", "meeting_id": 1})

    def test_update_2_actions(self) -> None:
        self.create_meeting(4)
        response = self.request_json(
            [
                {
                    "action": "meeting.update",
                    "data": [{"id": 1, "name": "name1_updated"}],
                },
                {
                    "action": "meeting.update",
                    "data": [{"id": 4, "name": "name2_updated"}],
                },
            ],
        )
        self.assert_status_code(response, 200)
        meeting1 = self.get_model("meeting/1")
        assert meeting1.get("name") == "name1_updated"
        meeting2 = self.get_model("meeting/4")
        assert meeting2.get("name") == "name2_updated"

    def test_update_1_2_events(self) -> None:
        self.create_meeting(4)
        response = self.request_multi(
            "meeting.update",
            [
                {"id": 1, "name": "name1_updated"},
                {"id": 4, "name": "name2_updated"},
            ],
        )
        self.assert_status_code(response, 200)
        meeting1 = self.get_model("meeting/1")
        assert meeting1.get("name") == "name1_updated"
        meeting2 = self.get_model("meeting/4")
        assert meeting2.get("name") == "name2_updated"

    def test_delete_2_actions(self) -> None:
        self.create_meeting(4)
        response = self.request_json(
            [
                {"action": "meeting.delete", "data": [{"id": 1}]},
                {"action": "meeting.delete", "data": [{"id": 4}]},
            ],
        )
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("meeting/1")
        self.assert_model_not_exists("meeting/4")
        self.assert_model_exists("committee/60", {"meeting_ids": None})

    def test_delete_1_2_events(self) -> None:
        self.create_meeting(4)
        response = self.request_multi("meeting.delete", [{"id": 1}, {"id": 4}])
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("meeting/1")
        self.assert_model_not_exists("meeting/4")
        self.assert_model_exists("committee/60", {"meeting_ids": None})
