from unittest import TestCase

from openslides_backend.actions.topic.actions import TopicCreate
from openslides_backend.actions.types import Payload
from openslides_backend.exceptions import ActionException


class TopicCreateTester(TestCase):
    def setUp(self) -> None:
        self.action = TopicCreate()

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

    def test_validation_correct(self) -> None:
        payload = [{"title": "title_ooPhi9ZohC", "text": "text_eeKoosahh4"}]
        self.action.validate(payload)
