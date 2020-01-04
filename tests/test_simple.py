from unittest import TestCase

from fastjsonschema import JsonSchemaException  # type: ignore

from openslides_backend.actions.topic.actions import TopicCreate
from openslides_backend.actions.types import Payload


class TopicCreateTester(TestCase):
    def setUp(self) -> None:
        self.action = TopicCreate()

    def test_validation_empty(self) -> None:
        payload: Payload = []
        with self.assertRaises(JsonSchemaException):
            self.action.validate(payload)

    def test_validation_empty_2(self) -> None:
        payload: Payload = [{}]
        with self.assertRaises(JsonSchemaException):
            self.action.validate(payload)

    def test_validation_fuzzy(self) -> None:
        payload = [{"wrong_field": "text_Kiofee1ieV"}]
        with self.assertRaises(JsonSchemaException):
            self.action.validate(payload)

    def test_validation_correct(self) -> None:
        payload = [{"title": "title_ooPhi9ZohC", "text": "text_eeKoosahh4"}]
        self.action.validate(payload)
