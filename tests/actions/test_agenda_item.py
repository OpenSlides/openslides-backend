from unittest import TestCase

from openslides_backend.actions.agenda_item.create import AgendaItemCreate
from openslides_backend.actions.agenda_item.delete import AgendaItemDelete
from openslides_backend.actions.agenda_item.update import AgendaItemUpdate

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
        self.valid_payload_update = [
            {"id": 3393211712, "content_object_id": "topic/1312354708"}
        ]
        self.valid_payload_delete = [{"id": 3393211712}]
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
        self.assertEqual(result, expected)

    def test_wsgi_request_create(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.post(
            "/",
            json=[{"action": "agenda_item.create", "data": self.valid_payload_create}],
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Action handled successfully", str(response.data))

    def test_perform_update(self) -> None:
        action = AgendaItemUpdate(PermissionTestAdapter(), DatabaseTestAdapter())
        write_request_elements = action.perform(
            self.valid_payload_update, user_id=self.user_id
        )
        result = list(write_request_elements)
        expected = [
            {
                "events": [
                    {
                        "type": "update",
                        "fqid": get_fqid("agenda_item/3393211712"),
                        "fields": {"content_object_id": get_fqid("topic/1312354708")},
                    },
                    {
                        "type": "update",
                        "fqid": get_fqid("topic/1312354708"),
                        "fields": {"agenda_item_id": 3393211712},
                    },
                    {
                        "type": "update",
                        "fqid": get_fqid("topic/5756367535"),
                        "fields": {"agenda_item_id": None},
                    },
                ],
                "information": {
                    get_fqid("agenda_item/3393211712"): ["Object updated"],
                    get_fqid("topic/1312354708"): ["Object attached to agenda item"],
                    get_fqid("topic/5756367535"): [
                        "Object attachment to agenda item reset"
                    ],
                },
                "user_id": self.user_id,
                "locked_fields": {
                    get_fqfield("agenda_item/3393211712/deleted"): 1,
                    get_fqfield("topic/1312354708/agenda_item_id"): 1,
                    get_fqfield("topic/5756367535/agenda_item_id"): 1,
                },
            },
        ]
        self.assertEqual(result, expected)

    def test_wsgi_request_update(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.post(
            "/",
            json=[{"action": "agenda_item.update", "data": self.valid_payload_update}],
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Action handled successfully", str(response.data))

    def test_perform_delete(self) -> None:
        action = AgendaItemDelete(PermissionTestAdapter(), DatabaseTestAdapter())
        write_request_elements = action.perform(
            self.valid_payload_delete, user_id=self.user_id
        )
        result = list(write_request_elements)
        expected = [
            {
                "events": [
                    {"type": "delete", "fqid": get_fqid("agenda_item/3393211712")},
                    {
                        "type": "update",
                        "fqid": get_fqid("meeting/9079236097"),
                        "fields": {"agenda_item_ids": []},
                    },
                    {
                        "type": "update",
                        "fqid": get_fqid("topic/5756367535"),
                        "fields": {"agenda_item_id": None},
                    },
                ],
                "information": {
                    get_fqid("agenda_item/3393211712"): ["Object deleted"],
                    get_fqid("meeting/9079236097"): [
                        "Object attachment to agenda item reset"
                    ],
                    get_fqid("topic/5756367535"): [
                        "Object attachment to agenda item reset"
                    ],
                },
                "user_id": self.user_id,
                "locked_fields": {
                    get_fqfield("agenda_item/3393211712/deleted"): 1,
                    get_fqfield("meeting/9079236097/agenda_item_ids"): 1,
                    get_fqfield("topic/5756367535/agenda_item_id"): 1,
                },
            },
        ]
        self.assertEqual(result, expected)

    def test_wsgi_request_delete(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.post(
            "/",
            json=[{"action": "agenda_item.delete", "data": self.valid_payload_delete}],
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Action handled successfully", str(response.data))
