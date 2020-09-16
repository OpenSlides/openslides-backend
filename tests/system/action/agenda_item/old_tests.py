import simplejson as json

from tests.system.action.base import BaseActionTestCase
from tests.util import get_fqfield

# TODO: remove this file once adapted to the new schema.


class AgendaItemCreateUpdateDeleteTester(BaseActionTestCase):
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
        self.user_id = 5968705978

    def test_wsgi_request_create(self) -> None:
        expected_write_data = json.dumps(  # noqa: F841
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
        # client = Client(
        #     create_test_application(
        #         user_id=self.user_id,
        #         view_name="ActionView",
        #         superuser=self.user_id,
        #         datastore_content=self.datastore_content,
        #         expected_write_data=expected_write_data,
        #     ),
        #     ResponseWrapper,
        # )
        response = self.client.post(
            "/",
            json=[{"action": "agenda_item.create", "data": self.valid_payload_create}],
        )
        self.assert_status_code(response, 200)
        self.assertIn("Action handled successfully", str(response.data))

    def test_wsgi_request_update(self) -> None:
        expected_write_data = json.dumps(  # noqa: F841
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
        # client = Client(
        #     create_test_application(
        #         user_id=self.user_id,
        #         view_name="ActionView",
        #         superuser=self.user_id,
        #         datastore_content=self.datastore_content,
        #         expected_write_data=expected_write_data,
        #     ),
        #     ResponseWrapper,
        # )
        response = self.client.post(
            "/",
            json=[{"action": "agenda_item.update", "data": self.valid_payload_update}],
        )
        self.assert_status_code(response, 200)
        self.assertIn("Action handled successfully", str(response.data))

    def test_wsgi_request_delete(self) -> None:
        expected_write_data = json.dumps(  # noqa: F841
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
        # client = Client(
        #     create_test_application(
        #         user_id=self.user_id,
        #         view_name="ActionView",
        #         superuser=self.user_id,
        #         datastore_content=self.datastore_content,
        #         expected_write_data=expected_write_data,
        #     ),
        #     ResponseWrapper,
        # )
        response = self.client.post(
            "/",
            json=[{"action": "agenda_item.delete", "data": self.valid_payload_delete}],
        )
        self.assert_status_code(response, 200)
        self.assertIn("Action handled successfully", str(response.data))
