from unittest import TestCase

from openslides_backend.actions.topic.actions import TopicCreate
from openslides_backend.actions.types import Payload
from openslides_backend.exceptions import ActionException

from ..database import TESTDATA, DatabaseTestAdapter


class TopicCreateTester(TestCase):
    def setUp(self) -> None:
        self.action = TopicCreate(DatabaseTestAdapter())
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
                "attachments": self.attachments,
            }
        ]

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

    def test_prepare_dataset_1(self) -> None:
        dataset = self.action.prepare_dataset(self.valid_payload_1)
        self.assertEqual(dataset["position"], 1)
        self.assertEqual(
            dataset["data"],
            [
                {
                    "topic": self.valid_payload_1[0],
                    "new_id": 42,
                    "mediafile.attachment": [],
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
                    "mediafile.attachment": [
                        {"id": self.attachments[0], "topic_ids": []},
                        {"id": self.attachments[1], "topic_ids": []},
                    ],
                }
            ],
        )
