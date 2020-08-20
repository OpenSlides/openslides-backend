import simplejson as json

from openslides_backend.models.agenda_item import AgendaItem
from tests.system.action.base import BaseActionTestCase
from tests.util import get_fqfield


class AgendaItemNumberingTester(BaseActionTestCase):
    """
    Tests agenda item numbering action.
    """

    def setUp(self) -> None:
        super().setUp()
        self.create_model(
            "meeting/1", {"name": "name_dto8zaGeJ1u", "agenda_item_ids": [1, 2, 3]},
        )
        self.create_model(
            "agenda_item/1",
            {
                "id": 1,
                "meeting_id": 1,
                "item_number": "Old item numberUdeepoo7nu",
                "weight": 10,
                "type": 1,
            },
        )
        self.create_model(
            "agenda_item/2",
            {"id": 2, "meeting_id": 1, "weight": 10, "parent_id": 1, "type": 1},
        )
        self.create_model(
            "agenda_item/3",
            {"id": 3, "meeting_id": 1, "parent_id": 1, "weight": 10, "type": 1},
        )
        self.valid_payload = {"meeting_id": 1}
        self.user_id = (
            5968705978  # This user has perm TOPIC_CAN_MANAGE for some meetings.
        )

    def test_numbering(self) -> None:
        datastore_content = {  # noqa: F841
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
        expected_write_data = json.dumps(  # noqa: F841
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
        # client = Client(
        #     create_test_application(
        #         user_id=self.user_id,
        #         view_name="ActionView",
        #         superuser=self.user_id,
        #         datastore_content=datastore_content,
        #         expected_write_data=expected_write_data,
        #     ),
        #     ResponseWrapper,
        # )
        response = self.client.post(
            "/", json=[{"action": "agenda_item.numbering", "data": self.valid_payload}],
        )
        self.assert_status_code(response, 200)
        self.assertIn("Action handled successfully", str(response.data))

    def test_numbering_with_parents(self) -> None:
        datastore_content = {  # noqa: F841
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
        expected_write_data = json.dumps(  # noqa: F841
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
        # client = Client(
        #     create_test_application(
        #         user_id=self.user_id,
        #         view_name="ActionView",
        #         superuser=self.user_id,
        #         datastore_content=datastore_content,
        #         expected_write_data=expected_write_data,
        #     ),
        #     ResponseWrapper,
        # )
        response = self.client.post(
            "/", json=[{"action": "agenda_item.numbering", "data": self.valid_payload}],
        )
        self.assert_status_code(response, 200)
        self.assertIn("Action handled successfully", str(response.data))

    def test_numbering_with_non_public_items(self) -> None:
        datastore_content = {  # noqa: F841
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
        expected_write_data = json.dumps(  # noqa: F841
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
        # client = Client(
        #     create_test_application(
        #         user_id=self.user_id,
        #         view_name="ActionView",
        #         superuser=self.user_id,
        #         datastore_content=datastore_content,
        #         expected_write_data=expected_write_data,
        #     ),
        #     ResponseWrapper,
        # )
        response = self.client.post(
            "/", json=[{"action": "agenda_item.numbering", "data": self.valid_payload}],
        )
        self.assert_status_code(response, 200)
        self.assertIn("Action handled successfully", str(response.data))
