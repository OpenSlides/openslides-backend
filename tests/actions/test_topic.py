from unittest import TestCase
from unittest.mock import patch

from openslides_backend.actions.topic.actions import TopicCreate
from openslides_backend.actions.types import Payload
from openslides_backend.exceptions import ActionException
from openslides_backend.wsgi import application

from ..adapters.authentication import AuthenticationTestAdapter
from ..adapters.database import TESTDATA, DatabaseTestAdapter
from ..utils import Client, ResponseWrapper, get_fqfield


class TopicCreateActionTester(TestCase):
    def setUp(self) -> None:
        self.action = TopicCreate(DatabaseTestAdapter())
        self.user_id = 5968705978
        self.valid_payload_1 = [
            {"title": "title_ooPhi9ZohC", "text": "text_eeKoosahh4"}
        ]
        self.attachments = [
            TESTDATA[0]["id"],
            TESTDATA[1]["id"],
        ]
        self.valid_payload_2 = [
            {
                "title": "title_pha2Eirohg",
                "text": "text_CaekiiLai2",
                "mediafile_attachment_ids": self.attachments,
            }
        ]
        self.valid_payload_3 = [{"title": "title_eivaey2Aeg"}]

    def test_validation_empty(self) -> None:
        payload: Payload = []
        with self.assertRaises(ActionException):
            self.action.validate(payload)

    def test_validation_empty_2(self) -> None:
        payload: Payload = [{}]
        with self.assertRaises(ActionException):
            self.action.validate(payload)

    def test_validation_fuzzy(self) -> None:
        payload = [{"wrong_field": "text_Kiofee1ieV"}]
        with self.assertRaises(ActionException):
            self.action.validate(payload)

    def test_validation_correct_1(self) -> None:
        self.action.validate(self.valid_payload_1)

    def test_validation_correct_2(self) -> None:
        self.action.validate(self.valid_payload_2)

    def test_validation_correct_3(self) -> None:
        self.action.validate(self.valid_payload_3)

    def test_prepare_dataset_1(self) -> None:
        dataset = self.action.prepare_dataset(self.valid_payload_1)
        self.assertEqual(dataset["position"], 1)
        self.assertEqual(
            dataset["data"],
            [
                {
                    "topic": self.valid_payload_1[0],
                    "new_id": 42,
                    "mediafile_attachment": {},
                }
            ],
        )

    def test_prepare_dataset_2(self) -> None:
        dataset = self.action.prepare_dataset(self.valid_payload_2)
        self.assertEqual(dataset["position"], 1)
        self.assertEqual(
            dataset["data"],
            [
                {
                    "topic": self.valid_payload_2[0],
                    "new_id": 42,
                    "mediafile_attachment": {
                        self.attachments[0]: {"topic_ids": []},
                        self.attachments[1]: {"topic_ids": []},
                    },
                }
            ],
        )

    def test_prepare_dataset_3(self) -> None:
        dataset = self.action.prepare_dataset(self.valid_payload_3)
        self.assertEqual(dataset["position"], 1)
        self.assertEqual(
            dataset["data"],
            [
                {
                    "topic": self.valid_payload_3[0],
                    "new_id": 42,
                    "mediafile_attachment": {},
                }
            ],
        )

    def test_perform_empty(self) -> None:
        payload: Payload = []
        with self.assertRaises(ActionException):
            self.action.perform(payload, user_id=self.user_id)

    def test_perform_empty_2(self) -> None:
        payload: Payload = [{}]
        with self.assertRaises(ActionException):
            self.action.perform(payload, user_id=self.user_id)

    def test_perform_fuzzy(self) -> None:
        payload = [{"wrong_field": "text_Kiofee1ieV"}]
        with self.assertRaises(ActionException):
            self.action.perform(payload, user_id=self.user_id)

    def test_perform_correct_1(self) -> None:
        events = self.action.perform(self.valid_payload_1, user_id=self.user_id)
        self.assertEqual(
            list(events),
            [
                {
                    "type": "create",
                    "position": 1,
                    "information": {"user_id": self.user_id, "text": "Topic created"},
                    "fields": {
                        get_fqfield("topic/42/title"): "title_ooPhi9ZohC",
                        get_fqfield("topic/42/text"): "text_eeKoosahh4",
                    },
                }
            ],
        )

    def test_perform_correct_2(self) -> None:
        events = self.action.perform(self.valid_payload_2, user_id=self.user_id)
        self.assertEqual(
            list(events),
            [
                {
                    "type": "create",
                    "position": 1,
                    "information": {"user_id": self.user_id, "text": "Topic created"},
                    "fields": {
                        get_fqfield("topic/42/title"): "title_pha2Eirohg",
                        get_fqfield("topic/42/text"): "text_CaekiiLai2",
                        get_fqfield(
                            "topic/42/mediafile_attachment_ids"
                        ): self.attachments,
                    },
                },
                {
                    "type": "update",
                    "position": 1,
                    "information": {
                        "user_id": self.user_id,
                        "text": "Mediafile attached to new topic.",
                    },
                    "fields": {
                        get_fqfield(
                            f"mediafile_attachment/{self.attachments[0]}/topic_ids"
                        ): [42]
                    },
                },
                {
                    "type": "update",
                    "position": 1,
                    "information": {
                        "user_id": self.user_id,
                        "text": "Mediafile attached to new topic.",
                    },
                    "fields": {
                        get_fqfield(
                            f"mediafile_attachment/{self.attachments[1]}/topic_ids"
                        ): [42]
                    },
                },
            ],
        )

    def test_perform_correct_3(self) -> None:
        events = self.action.perform(self.valid_payload_3, user_id=self.user_id)
        self.assertEqual(
            list(events),
            [
                {
                    "type": "create",
                    "position": 1,
                    "information": {"user_id": self.user_id, "text": "Topic created"},
                    "fields": {get_fqfield("topic/42/title"): "title_eivaey2Aeg"},
                }
            ],
        )

    @patch(
        "openslides_backend.views.action_view.AuthenticationAdapter",
        AuthenticationTestAdapter,
    )
    def test_wsgi_request_empty(self) -> None:
        client = Client(application, ResponseWrapper)
        response = client.post(
            "/system/api/actions", json=[{"action": "topic.create", "data": [{}]}]
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "data[0] must contain [\\'title\\'] properties", str(response.data)
        )

    @patch(
        "openslides_backend.views.action_view.AuthenticationAdapter",
        AuthenticationTestAdapter,
    )
    def test_wsgi_request_fuzzy(self) -> None:
        client = Client(application, ResponseWrapper)
        response = client.post(
            "/system/api/actions",
            json=[
                {"action": "topic.create", "data": [{"wrong_field": "text_Hoh3quoos9"}]}
            ],
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "data[0] must contain [\\'title\\'] properties", str(response.data)
        )

    @patch(
        "openslides_backend.views.action_view.AuthenticationAdapter",
        AuthenticationTestAdapter,
    )
    @patch("openslides_backend.views.action_view.DatabaseAdapter", DatabaseTestAdapter)
    def test_wsgi_request_correct_1(self) -> None:
        client = Client(application, ResponseWrapper)
        response = client.post(
            "/system/api/actions",
            json=[{"action": "topic.create", "data": self.valid_payload_1}],
        )
        self.assertEqual(response.status_code, 200)

    @patch(
        "openslides_backend.views.action_view.AuthenticationAdapter",
        AuthenticationTestAdapter,
    )
    @patch("openslides_backend.views.action_view.DatabaseAdapter", DatabaseTestAdapter)
    def test_wsgi_request_correct_2(self) -> None:
        client = Client(application, ResponseWrapper)
        response = client.post(
            "/system/api/actions",
            json=[{"action": "topic.create", "data": self.valid_payload_2}],
        )
        self.assertEqual(response.status_code, 200)

    @patch(
        "openslides_backend.views.action_view.AuthenticationAdapter",
        AuthenticationTestAdapter,
    )
    @patch("openslides_backend.views.action_view.DatabaseAdapter", DatabaseTestAdapter)
    def test_wsgi_request_correct_3(self) -> None:
        client = Client(application, ResponseWrapper)
        response = client.post(
            "/system/api/actions",
            json=[{"action": "topic.create", "data": self.valid_payload_3}],
        )
        self.assertEqual(response.status_code, 200)
