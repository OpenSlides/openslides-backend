from unittest import TestCase
from unittest.mock import Mock

from openslides_backend.action.action_handler import ActionHandler
from openslides_backend.action.util.typing import Payload

"""
ACHTUNG !!!!!!!!!!!!!!!!!!!!!!!!!!!!!

Angefangen zum PullRequest #424 Adjust WR to per-action-base with locked fields
Joshau sieht in als Unittest, ist aber eher ein system-Test, da er
mindestens den Datastore-Service braucht, um seine WriteRequests zu erzeugen

"""


class ActionHandlerTester(TestCase):
    """
    Tests methods of ActionHandler class
    """

    def setUp(self) -> None:
        logger = Mock()
        services = Mock()
        self.action_handler = ActionHandler(services, logger)
        self.action_handler.user_id = 1

    def test_parse_actions_create_2_actions(self) -> None:
        self.datastore.create_model("committee/1", {"name": "test_committee"})
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

        write_requests, _ = self.action_handler.parse_actions(payload)
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
        self.datastore.create_model("committee/1", {"name": "test_committee"})
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

        write_requests, _ = self.action_handler.parse_actions(payload)
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
