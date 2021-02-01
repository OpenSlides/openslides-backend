from unittest.mock import Mock

from openslides_backend.action.action_handler import ActionHandler
from openslides_backend.action.util.typing import Payload

from .base import BaseActionTestCase

# TODO: parse_action Tests als UnitTests zum Action Handler, die anderen, die das schreib format testen mal schauen


class GeneralActionCommandFormat(BaseActionTestCase):
    """
    Tests the interface to datastore-command with one WriteRequest
    per payload-action and it's own locked_fields
    """

    def get_action_handler(self) -> ActionHandler:
        logger = Mock()
        handler = ActionHandler(self.services, logger)
        handler.user_id = 1
        return handler

    def test_parse_actions_create_2_actions(self) -> None:
        self.create_model("committee/1", {"name": "test_committee"})
        payload: Payload = [
            {
                "action": "meeting.create",
                "data": [
                    {
                        "name": "name1",
                        "welcome_title": "title1",
                        "committee_id": 1,
                    }
                ],
            },
            {
                "action": "meeting.create",
                "data": [
                    {
                        "name": "name2",
                        "welcome_title": "title2",
                        "committee_id": 1,
                    }
                ],
            },
        ]

        action_handler = self.get_action_handler()
        write_requests, _ = action_handler.parse_actions(payload)
        self.assertEqual(len(write_requests), 2)
        self.assertEqual(len(write_requests[0].events), 2)
        self.assertEqual(write_requests[0].locked_fields, {"committee/1": 2})
        self.assertEqual(write_requests[0].events[0]["type"], "create")
        self.assertEqual(write_requests[0].events[1]["type"], "update")
        self.assertEqual(str(write_requests[0].events[0]["fqid"]), "meeting/1")
        self.assertEqual(str(write_requests[0].events[1]["fqid"]), "committee/1")
        self.assertEqual(len(write_requests[1].events), 2)
        self.assertEqual(write_requests[1].locked_fields, {"committee/1": 2})

    def test_parse_actions_create_1_2_events(self) -> None:
        self.create_model("committee/1", {"name": "test_committee"})
        payload: Payload = [
            {
                "action": "meeting.create",
                "data": [
                    {
                        "name": "name1",
                        "welcome_title": "title1",
                        "committee_id": 1,
                    },
                    {
                        "name": "name2",
                        "welcome_title": "title2",
                        "committee_id": 1,
                    },
                ],
            },
        ]

        action_handler = self.get_action_handler()
        write_requests, _ = action_handler.parse_actions(payload)
        self.assertEqual(len(write_requests), 1)
        self.assertEqual(len(write_requests[0].events), 4)
        self.assertEqual(write_requests[0].locked_fields, {"committee/1": 2})
        self.assertEqual(write_requests[0].events[0]["type"], "create")
        self.assertEqual(write_requests[0].events[1]["type"], "create")
        self.assertEqual(write_requests[0].events[2]["type"], "update")
        self.assertEqual(write_requests[0].events[3]["type"], "update")
        self.assertEqual(str(write_requests[0].events[0]["fqid"]), "meeting/1")
        self.assertEqual(str(write_requests[0].events[1]["fqid"]), "meeting/2")
        self.assertEqual(str(write_requests[0].events[2]["fqid"]), "committee/1")
        self.assertEqual(str(write_requests[0].events[3]["fqid"]), "committee/1")

    def test_create_2_actions(self) -> None:
        self.create_model("committee/1", {"name": "test_committee"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "meeting.create",
                    "data": [
                        {
                            "name": "name1",
                            "welcome_title": "title1",
                            "committee_id": 1,
                        }
                    ],
                },
                {
                    "action": "meeting.create",
                    "data": [
                        {
                            "name": "name2",
                            "welcome_title": "title2",
                            "committee_id": 1,
                        }
                    ],
                },
            ],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            b"{\"success\": false, \"message\": \"Datastore service sends HTTP 400. {'key': 'committee/1', 'type': 6, 'type_verbose': 'MODEL_LOCKED'}\"}",
            response.data,
        )
        self.assert_model_not_exists("meeting/1")
        self.assert_model_not_exists("meeting/1")
        self.assert_model_exists("committee/1", {"meeting_ids": None})

    def test_create_1_2_events(self) -> None:
        self.create_model("committee/1", {"name": "test_committee"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "meeting.create",
                    "data": [
                        {
                            "name": "name1",
                            "welcome_title": "title1",
                            "committee_id": 1,
                        },
                        {
                            "name": "name2",
                            "welcome_title": "title2",
                            "committee_id": 1,
                        },
                    ],
                },
            ],
        )
        self.assert_status_code(response, 200)
        meeting1 = self.get_model("meeting/1")
        assert meeting1.get("name") == "name1"
        assert meeting1.get("committee_id") == 1
        meeting2 = self.get_model("meeting/2")
        assert meeting2.get("name") == "name2"
        assert meeting2.get("committee_id") == 1

    def test_update_2_actions(self) -> None:
        self.create_model(
            "meeting/1", {"name": "name1", "committee_id": 1, "welcome_title": "t"}
        )
        self.create_model(
            "meeting/2", {"name": "name2", "committee_id": 1, "welcome_title": "t"}
        )
        self.create_model("committee/1", {"name": "test_committee"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "meeting.update",
                    "data": [
                        {
                            "id": 1,
                            "name": "name1_updated",
                        }
                    ],
                },
                {
                    "action": "meeting.update",
                    "data": [
                        {
                            "id": 2,
                            "name": "name2_updated",
                        }
                    ],
                },
            ],
        )
        self.assert_status_code(response, 200)
        meeting1 = self.get_model("meeting/1")
        assert meeting1.get("name") == "name1_updated"
        meeting2 = self.get_model("meeting/2")
        assert meeting2.get("name") == "name2_updated"

    def test_update_1_2_events(self) -> None:
        self.create_model(
            "meeting/1", {"name": "name1", "committee_id": 1, "welcome_title": "t"}
        )
        self.create_model(
            "meeting/2", {"name": "name2", "committee_id": 1, "welcome_title": "t"}
        )
        self.create_model("committee/1", {"name": "test_committee"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "meeting.update",
                    "data": [
                        {
                            "id": 1,
                            "name": "name1_updated",
                        },
                        {
                            "id": 2,
                            "name": "name2_updated",
                        },
                    ],
                },
            ],
        )
        self.assert_status_code(response, 200)
        meeting1 = self.get_model("meeting/1")
        assert meeting1.get("name") == "name1_updated"
        meeting2 = self.get_model("meeting/2")
        assert meeting2.get("name") == "name2_updated"

    def test_delete_2_actions(self) -> None:
        self.create_model(
            "meeting/1", {"name": "name1", "committee_id": 1, "welcome_title": "t"}
        )
        self.create_model(
            "meeting/2", {"name": "name2", "committee_id": 1, "welcome_title": "t"}
        )
        self.create_model(
            "committee/1", {"name": "test_committee", "meeting_ids": [1, 2]}
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "meeting.delete",
                    "data": [
                        {
                            "id": 1,
                        }
                    ],
                },
                {
                    "action": "meeting.delete",
                    "data": [
                        {
                            "id": 2,
                        }
                    ],
                },
            ],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            b"{\"success\": false, \"message\": \"Datastore service sends HTTP 400. {'key': 'committee/1', 'type': 6, 'type_verbose': 'MODEL_LOCKED'}\"}",
            response.data,
        )
        self.assert_model_exists("meeting/1")
        self.assert_model_exists("meeting/2")

    def test_delete_1_2_events(self) -> None:
        self.create_model(
            "meeting/1", {"name": "name1", "committee_id": 1, "welcome_title": "t"}
        )
        self.create_model(
            "meeting/2", {"name": "name2", "committee_id": 1, "welcome_title": "t"}
        )
        self.create_model(
            "committee/1", {"name": "test_committee", "meeting_ids": [1, 2]}
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "meeting.delete",
                    "data": [
                        {
                            "id": 1,
                        },
                        {
                            "id": 2,
                        },
                    ],
                },
            ],
        )
        self.assert_status_code(response, 200)
        self.assert_model_deleted("meeting/1")
        self.assert_model_deleted("meeting/2")
