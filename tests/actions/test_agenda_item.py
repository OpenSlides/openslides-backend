from unittest import TestCase

import simplejson as json

from openslides_backend.actions.agenda_item.create import AgendaItemCreate
from openslides_backend.actions.agenda_item.delete import AgendaItemDelete
from openslides_backend.actions.agenda_item.update import AgendaItemUpdate
from openslides_backend.models.agenda_item import AgendaItem

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
        self.datastore_content = {
            get_fqfield("meeting/7816466305/name"): "name_dei9iPh9fi",
            get_fqfield("meeting/9079236097/topic_ids"): [5756367535],
            get_fqfield("meeting/9079236097/agenda_item_ids"): [3393211712],
            get_fqfield("topic/1312354708/title"): "title_eeWa8oenii",
            get_fqfield("topic/5756367535/meeting_id"): 9079236097,
            get_fqfield("topic/5756367535/agenda_item_id"): 3393211712,
            get_fqfield("agenda_item/3393211712/meeting_id"): 9079236097,
            get_fqfield("agenda_item/3393211712/content_object_id"): "topic/5756367535",
        }
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

    def test_perform_create(self) -> None:
        action = AgendaItemCreate(
            PermissionTestAdapter(),
            DatabaseTestAdapter(datastore_content=self.datastore_content),
        )
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
            },
        ]
        self.assertEqual(result, expected)

    def test_wsgi_request_create(self) -> None:
        expected_write_data = json.dumps(
            {
                "events": [
                    {
                        "type": "create",
                        "fqid": "agenda_item/42",
                        "fields": {
                            "meeting_id": 7816466305,
                            "content_object_id": "topic/1312354708",
                        },
                    },
                    {
                        "type": "update",
                        "fqid": "meeting/7816466305",
                        "fields": {"agenda_item_ids": [42]},
                    },
                    {
                        "type": "update",
                        "fqid": "topic/1312354708",
                        "fields": {"agenda_item_id": 42},
                    },
                ],
                "information": {
                    "agenda_item/42": ["Object created"],
                    "meeting/7816466305": ["Object attached to agenda item"],
                    "topic/1312354708": ["Object attached to agenda item"],
                },
                "user_id": self.user_id,
                "locked_fields": {"meeting/7816466305": 1, "topic/1312354708": 1},
            }
        )
        client = Client(
            create_test_application(
                user_id=self.user_id,
                view_name="ActionsView",
                datastore_content=self.datastore_content,
                expected_write_data=expected_write_data,
            ),
            ResponseWrapper,
        )
        response = client.post(
            "/",
            json=[{"action": "agenda_item.create", "data": self.valid_payload_create}],
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Action handled successfully", str(response.data))

    def test_perform_update(self) -> None:
        action = AgendaItemUpdate(
            PermissionTestAdapter(),
            DatabaseTestAdapter(datastore_content=self.datastore_content),
        )
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
            },
        ]
        self.assertEqual(result, expected)

    def test_wsgi_request_update(self) -> None:
        expected_write_data = json.dumps(
            {
                "events": [
                    {
                        "type": "update",
                        "fqid": "agenda_item/3393211712",
                        "fields": {"content_object_id": "topic/1312354708"},
                    },
                    {
                        "type": "update",
                        "fqid": "topic/1312354708",
                        "fields": {"agenda_item_id": 3393211712},
                    },
                    {
                        "type": "update",
                        "fqid": "topic/5756367535",
                        "fields": {"agenda_item_id": None},
                    },
                ],
                "information": {
                    "agenda_item/3393211712": ["Object updated"],
                    "topic/1312354708": ["Object attached to agenda item"],
                    "topic/5756367535": ["Object attachment to agenda item reset"],
                },
                "user_id": self.user_id,
                "locked_fields": {
                    "agenda_item/3393211712": 1,
                    "topic/5756367535": 1,
                    "topic/1312354708": 1,
                },
            }
        )
        client = Client(
            create_test_application(
                user_id=self.user_id,
                view_name="ActionsView",
                datastore_content=self.datastore_content,
                expected_write_data=expected_write_data,
            ),
            ResponseWrapper,
        )
        response = client.post(
            "/",
            json=[{"action": "agenda_item.update", "data": self.valid_payload_update}],
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Action handled successfully", str(response.data))

    def test_perform_delete(self) -> None:
        action = AgendaItemDelete(
            PermissionTestAdapter(),
            DatabaseTestAdapter(datastore_content=self.datastore_content),
        )
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
            },
        ]
        self.assertEqual(result, expected)

    def test_wsgi_request_delete(self) -> None:
        expected_write_data = json.dumps(
            {
                "events": [
                    {"type": "delete", "fqid": "agenda_item/3393211712"},
                    {
                        "type": "update",
                        "fqid": "meeting/9079236097",
                        "fields": {"agenda_item_ids": []},
                    },
                    {
                        "type": "update",
                        "fqid": "topic/5756367535",
                        "fields": {"agenda_item_id": None},
                    },
                ],
                "information": {
                    "agenda_item/3393211712": ["Object deleted"],
                    "meeting/9079236097": ["Object attachment to agenda item reset"],
                    "topic/5756367535": ["Object attachment to agenda item reset"],
                },
                "user_id": self.user_id,
                "locked_fields": {
                    "agenda_item/3393211712": 1,
                    "meeting/9079236097": 1,
                    "topic/5756367535": 1,
                },
            }
        )
        client = Client(
            create_test_application(
                user_id=self.user_id,
                view_name="ActionsView",
                datastore_content=self.datastore_content,
                expected_write_data=expected_write_data,
            ),
            ResponseWrapper,
        )
        response = client.post(
            "/",
            json=[{"action": "agenda_item.delete", "data": self.valid_payload_delete}],
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Action handled successfully", str(response.data))


class AgendaItemNumberingTester(TestCase):
    """
    Tests agenda item numbering action.
    """

    def setUp(self) -> None:
        self.valid_payload = {"meeting_id": 2253238351}
        self.user_id = (
            5968705978  # This user has perm TOPIC_CAN_MANAGE for some meetings.
        )

    def test_wsgi_request_numbering(self) -> None:
        datastore_content = {
            get_fqfield("meeting/2253238351/name"): "name_dto8zaGeJ1u",
            get_fqfield("meeting/2253238351/agenda_item_ids"): [
                2442036319,
                3454829654,
                8500020949,
            ],
            get_fqfield("agenda_item/2442036319/meeting_id"): 2253238351,
            get_fqfield(
                "agenda_item/2442036319/item_number"
            ): "Old item numberUdeepoo7nu",
            get_fqfield("agenda_item/2442036319/weight"): 10,
            get_fqfield("agenda_item/3454829654/meeting_id"): 2253238351,
            get_fqfield("agenda_item/3454829654/weight"): 10,
            get_fqfield("agenda_item/3454829654/parent_id"): 2442036319,
            get_fqfield("agenda_item/8500020949/meeting_id"): 2253238351,
            get_fqfield("agenda_item/8500020949/parent_id"): 2442036319,
        }
        expected_write_data = json.dumps(
            {
                "events": [
                    {
                        "type": "update",
                        "fqid": "agenda_item/2442036319",
                        "fields": {"item_number": "1"},
                    },
                    {
                        "type": "update",
                        "fqid": "agenda_item/8500020949",
                        "fields": {"item_number": "1.1"},
                    },
                    {
                        "type": "update",
                        "fqid": "agenda_item/3454829654",
                        "fields": {"item_number": "1.2"},
                    },
                ],
                "information": {
                    "agenda_item/2442036319": ["Object updated"],
                    "agenda_item/3454829654": ["Object updated"],
                    "agenda_item/8500020949": ["Object updated"],
                },
                "user_id": self.user_id,
                "locked_fields": {
                    "agenda_item/2442036319": 1,
                    "agenda_item/3454829654": 1,
                    "agenda_item/8500020949": 1,
                },
            }
        )
        client = Client(
            create_test_application(
                user_id=self.user_id,
                view_name="ActionsView",
                datastore_content=datastore_content,
                expected_write_data=expected_write_data,
            ),
            ResponseWrapper,
        )
        response = client.post(
            "/", json=[{"action": "agenda_item.numbering", "data": self.valid_payload}],
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Action handled successfully", str(response.data))

    def test_wsgi_request_numbering_with_parents(self) -> None:
        datastore_content = {
            get_fqfield("meeting/2253238351/name"): "name_dto8zaGeJ1u",
            get_fqfield("meeting/2253238351/agenda_item_ids"): [
                2442036319,
                3454829654,
            ],
            get_fqfield("agenda_item/2442036319/meeting_id"): 2253238351,
            get_fqfield(
                "agenda_item/2442036319/item_number"
            ): "Old item numberUdeepoo7nu",
            get_fqfield("agenda_item/2442036319/weight"): 10,
            get_fqfield("agenda_item/3454829654/meeting_id"): 2253238351,
        }
        expected_write_data = json.dumps(
            {
                "events": [
                    {
                        "type": "update",
                        "fqid": "agenda_item/3454829654",
                        "fields": {"item_number": "1"},
                    },
                    {
                        "type": "update",
                        "fqid": "agenda_item/2442036319",
                        "fields": {"item_number": "2"},
                    },
                ],
                "information": {
                    "agenda_item/2442036319": ["Object updated"],
                    "agenda_item/3454829654": ["Object updated"],
                },
                "user_id": self.user_id,
                "locked_fields": {
                    "agenda_item/2442036319": 1,
                    "agenda_item/3454829654": 1,
                },
            }
        )
        client = Client(
            create_test_application(
                user_id=self.user_id,
                view_name="ActionsView",
                datastore_content=datastore_content,
                expected_write_data=expected_write_data,
            ),
            ResponseWrapper,
        )
        response = client.post(
            "/", json=[{"action": "agenda_item.numbering", "data": self.valid_payload}],
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Action handled successfully", str(response.data))

    def test_wsgi_request_numbering_with_non_public_items(self) -> None:
        datastore_content = {
            get_fqfield("meeting/2253238351/name"): "name_dto8zaGeJ1u",
            get_fqfield("meeting/2253238351/agenda_item_ids"): [
                2442036319,
                3454829654,
            ],
            get_fqfield("agenda_item/2442036319/meeting_id"): 2253238351,
            get_fqfield("agenda_item/2442036319/type"): AgendaItem.INTERNAL_ITEM,
            get_fqfield(
                "agenda_item/2442036319/item_number"
            ): "Old item numberUdeepoo7nu",
            get_fqfield("agenda_item/3454829654/meeting_id"): 2253238351,
        }
        expected_write_data = json.dumps(
            {
                "events": [
                    {
                        "type": "update",
                        "fqid": "agenda_item/3454829654",
                        "fields": {"item_number": "1"},
                    },
                    {
                        "type": "update",
                        "fqid": "agenda_item/2442036319",
                        "fields": {"item_number": ""},
                    },
                ],
                "information": {
                    "agenda_item/2442036319": ["Object updated"],
                    "agenda_item/3454829654": ["Object updated"],
                },
                "user_id": self.user_id,
                "locked_fields": {
                    "agenda_item/2442036319": 1,
                    "agenda_item/3454829654": 1,
                },
            }
        )
        client = Client(
            create_test_application(
                user_id=self.user_id,
                view_name="ActionsView",
                datastore_content=datastore_content,
                expected_write_data=expected_write_data,
            ),
            ResponseWrapper,
        )
        response = client.post(
            "/", json=[{"action": "agenda_item.numbering", "data": self.valid_payload}],
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Action handled successfully", str(response.data))
