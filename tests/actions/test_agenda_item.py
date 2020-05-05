from unittest import TestCase

from openslides_backend.actions.agenda_item.create import AgendaItemCreate

from ..fake_services.database import DatabaseTestAdapter
from ..fake_services.permission import PermissionTestAdapter
from ..utils import (
    Client,
    ResponseWrapper,
    create_test_application,
    get_fqfield,
    get_fqid,
)


class AgendaItemCreateUpdateDeleteTester(TestCase):
    """
    Tests agenda item create, update and delete action.
    """

    def setUp(self) -> None:
        self.valid_payload_create = [
            {"meeting_id": 7816466305, "content_object_id": "topic/1312354708"}
        ]

        self.user_id = (
            5968705978  # This user has perm TOPIC_CAN_MANAGE for some meetings.
        )
        self.application = create_test_application(
            user_id=self.user_id, view_name="ActionsView"
        )

    def test_perform_create(self) -> None:
        action = AgendaItemCreate(PermissionTestAdapter(), DatabaseTestAdapter())
        write_request_elements = action.perform(
            self.valid_payload_create, user_id=self.user_id
        )
        result = list(write_request_elements)
        expected = [
            {
                "events": [
                    {
                        "type": "create",
                        "fqid": get_fqid("agenda_item/42"),
                        "fields": {
                            "meeting_id": 7816466305,
                            "content_object_id": get_fqid("topic/1312354708"),
                        },
                    },
                    {
                        "type": "update",
                        "fqid": get_fqid("meeting/7816466305"),
                        "fields": {"agenda_item_ids": [42]},
                    },
                    {
                        "type": "update",
                        "fqid": get_fqid("topic/1312354708"),
                        "fields": {"agenda_item_id": 42},
                    },
                ],
                "information": {
                    get_fqid("agenda_item/42"): ["Object created"],
                    get_fqid("meeting/7816466305"): ["Object attached to agenda item"],
                    get_fqid("topic/1312354708"): ["Object attached to agenda item"],
                },
                "user_id": self.user_id,
                "locked_fields": {
                    get_fqfield("meeting/7816466305/agenda_item_ids"): 1,
                    get_fqfield("topic/1312354708/agenda_item_id"): 1,
                },
            },
        ]
        self.maxDiff = None
        self.assertEqual(result, expected)

    def test_wsgi_request_create(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.post(
            "/",
            json=[{"action": "agenda_item.create", "data": self.valid_payload_create}],
        )
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Action handled successfully", str(response.data))
