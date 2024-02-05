from unittest.mock import Mock

from openslides_backend.action.action_handler import ActionHandler
from openslides_backend.action.util.typing import Payload

from .base import BaseActionTestCase


class GeneralActionCommandFormat(BaseActionTestCase):
    """
    Tests the interface to datastore-command with one WriteRequest
    per payload-action and it's own locked_fields
    """

    def get_action_handler(self) -> ActionHandler:
        logger = Mock()
        config = Mock()
        handler = ActionHandler(config, self.services, logger)
        handler.user_id = 1
        handler.internal = False
        return handler

    def test_parse_actions_create_2_actions(self) -> None:
        self.create_model(
            "meeting/1", {"name": "meeting1", "is_active_in_organization_id": 1}
        )
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
        write_requests, _ = action_handler.parse_actions(payload)
        self.assertEqual(len(write_requests), 2)
        self.assertEqual(len(write_requests[0].events), 2)
        self.assertCountEqual(
            write_requests[0].locked_fields.keys(),
            [
                "group/weight",
                "meeting/1/group_ids",
            ],
        )
        self.assertEqual(write_requests[0].events[0]["type"], "create")
        self.assertEqual(write_requests[0].events[1]["type"], "update")
        self.assertEqual(str(write_requests[0].events[0]["fqid"]), "group/1")
        self.assertEqual(str(write_requests[0].events[1]["fqid"]), "meeting/1")
        self.assertEqual(len(write_requests[1].events), 2)
        self.assertCountEqual(
            write_requests[1].locked_fields.keys(),
            [
                "group/weight",
            ],
        )

    def test_parse_actions_create_1_2_events(self) -> None:
        self.create_model(
            "meeting/1", {"name": "meeting1", "is_active_in_organization_id": 1}
        )
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
        write_requests, _ = action_handler.parse_actions(payload)
        self.assertEqual(len(write_requests), 1)
        self.assertEqual(len(write_requests[0].events), 3)
        self.assertCountEqual(
            write_requests[0].locked_fields.keys(),
            [
                "group/weight",
                "meeting/1/group_ids",
            ],
        )
        self.assertEqual(write_requests[0].events[0]["type"], "create")
        self.assertEqual(write_requests[0].events[1]["type"], "create")
        self.assertEqual(write_requests[0].events[2]["type"], "update")
        self.assertEqual(str(write_requests[0].events[0]["fqid"]), "group/1")
        self.assertEqual(str(write_requests[0].events[1]["fqid"]), "group/2")
        self.assertEqual(str(write_requests[0].events[2]["fqid"]), "meeting/1")

    def test_create_2_actions(self) -> None:
        self.create_model(
            "meeting/1", {"name": "meeting1", "is_active_in_organization_id": 1}
        )
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
        self.assert_status_code(response, 400)
        self.assertIn(
            "Datastore service sends HTTP 400. The following locks were broken: 'group/weight'",
            response.json["message"],
        )
        self.assert_model_not_exists("group/1")
        self.assert_model_not_exists("group/2")
        self.assert_model_exists("meeting/1", {"group_ids": None})

    def test_create_1_2_events(self) -> None:
        self.create_model(
            "meeting/1", {"name": "meeting1", "is_active_in_organization_id": 1}
        )
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
        self.assert_model_exists("group/1", {"name": "group 1", "meeting_id": 1})
        self.assert_model_exists("group/2", {"name": "group 2", "meeting_id": 1})

    def test_update_2_actions(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "name": "name1",
                    "committee_id": 1,
                    "welcome_title": "t",
                    "is_active_in_organization_id": 1,
                },
                "meeting/2": {
                    "name": "name2",
                    "committee_id": 1,
                    "welcome_title": "t",
                    "is_active_in_organization_id": 1,
                },
                "committee/1": {"name": "test_committee"},
            }
        )
        response = self.request_json(
            [
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
        self.set_models(
            {
                "meeting/1": {
                    "name": "name1",
                    "committee_id": 1,
                    "welcome_title": "t",
                    "is_active_in_organization_id": 1,
                },
                "meeting/2": {
                    "name": "name2",
                    "committee_id": 1,
                    "welcome_title": "t",
                    "is_active_in_organization_id": 1,
                },
                "committee/1": {"name": "test_committee"},
            }
        )
        response = self.request_multi(
            "meeting.update",
            [
                {
                    "id": 1,
                    "name": "name1_updated",
                },
                {
                    "id": 2,
                    "name": "name2_updated",
                },
            ],
        )
        self.assert_status_code(response, 200)
        meeting1 = self.get_model("meeting/1")
        assert meeting1.get("name") == "name1_updated"
        meeting2 = self.get_model("meeting/2")
        assert meeting2.get("name") == "name2_updated"

    def test_delete_2_actions(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "name": "name1",
                    "committee_id": 1,
                    "welcome_title": "t",
                    "is_active_in_organization_id": 1,
                },
                "meeting/2": {
                    "name": "name2",
                    "committee_id": 1,
                    "welcome_title": "t",
                    "is_active_in_organization_id": 1,
                },
                "committee/1": {"name": "test_committee", "meeting_ids": [1, 2]},
            }
        )
        response = self.request_json(
            [
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
        self.assert_status_code(response, 200)
        self.assert_model_deleted("meeting/1")
        self.assert_model_deleted("meeting/2")
        self.assert_model_exists("committee/1", {"meeting_ids": []})

    def test_delete_1_2_events(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "name": "name1",
                    "committee_id": 1,
                    "welcome_title": "t",
                    "is_active_in_organization_id": 1,
                },
                "meeting/2": {
                    "name": "name2",
                    "committee_id": 1,
                    "welcome_title": "t",
                    "is_active_in_organization_id": 1,
                },
                "committee/1": {"name": "test_committee", "meeting_ids": [1, 2]},
            }
        )
        response = self.request_multi(
            "meeting.delete",
            [
                {
                    "id": 1,
                },
                {
                    "id": 2,
                },
            ],
        )
        self.assert_status_code(response, 200)
        self.assert_model_deleted("meeting/1")
        self.assert_model_deleted("meeting/2")
        self.assert_model_exists("committee/1", {"meeting_ids": []})
