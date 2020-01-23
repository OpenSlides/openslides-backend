from unittest import TestCase

from openslides_backend.actions import Payload
from openslides_backend.actions.meeting.create import MeetingCreate
from openslides_backend.shared.exceptions import ActionException, PermissionDenied

from ..fake_services.database import DatabaseTestAdapter
from ..fake_services.permission import PermissionTestAdapter
from ..utils import (
    Client,
    ResponseWrapper,
    create_test_application,
    get_fqfield,
    get_fqid,
)


class BaseMeetingCreateActionTester(TestCase):
    """
    Tests the meeting create action.
    """

    def setUp(self) -> None:
        self.valid_payload_1 = [
            {"committee_id": 5914213969, "title": "title_zusae6aD0a"}
        ]


class MeetingCreateActionUnitTester(BaseMeetingCreateActionTester):
    def setUp(self) -> None:
        super().setUp()
        self.action = MeetingCreate(PermissionTestAdapter(), DatabaseTestAdapter())
        self.action.user_id = (
            7121641734  # This user has perm MEETING_CAN_MANAGE for some committees.
        )

    def test_validation_empty(self) -> None:
        payload: Payload = []
        with self.assertRaises(ActionException):
            self.action.validate(payload)

    def test_validation_empty_2(self) -> None:
        payload: Payload = [{}]
        with self.assertRaises(ActionException):
            self.action.validate(payload)

    def test_validation_fuzzy(self) -> None:
        payload = [{"wrong_field": "text_aeBiPei0xi"}]
        with self.assertRaises(ActionException):
            self.action.validate(payload)

    def test_validation_correct_1(self) -> None:
        self.action.validate(self.valid_payload_1)

    def test_prepare_dataset_1(self) -> None:
        dataset = self.action.prepare_dataset(self.valid_payload_1)
        self.assertEqual(dataset["position"], 1)
        self.assertEqual(
            dataset["data"],
            [
                {
                    "meeting": self.valid_payload_1[0],
                    "new_id": 42,
                    "references": {
                        get_fqfield("committee/5914213969/meeting_ids"): {
                            "type": "add",
                            "value": [42],
                        },
                    },
                }
            ],
        )


class MeetingCreateActionPerformTester(BaseMeetingCreateActionTester):
    def setUp(self) -> None:
        super().setUp()
        self.action = MeetingCreate(PermissionTestAdapter(), DatabaseTestAdapter())
        self.user_id = (
            7121641734  # This user has perm MEETING_CAN_MANAGE for some committees.
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
        payload = [{"wrong_field": "text_Ohgahc3ieb"}]
        with self.assertRaises(ActionException):
            self.action.perform(payload, user_id=self.user_id)

    def test_perform_correct_1(self) -> None:
        write_request_elements = self.action.perform(
            self.valid_payload_1, user_id=self.user_id
        )
        self.assertEqual(
            list(write_request_elements),
            [
                {
                    "events": [
                        {
                            "type": "create",
                            "fqfields": {
                                get_fqfield("meeting/42/committee_id"): 5914213969,
                                get_fqfield("meeting/42/title"): "title_zusae6aD0a",
                            },
                        },
                        {
                            "type": "update",
                            "fqfields": {
                                get_fqfield("committee/5914213969/meeting_ids"): [42]
                            },
                        },
                    ],
                    "information": {
                        get_fqid("meeting/42"): ["Meeting created"],
                        get_fqid("committee/5914213969"): [
                            "Object attached to meeting"
                        ],
                    },
                    "user_id": self.user_id,
                    "locked_fields": {
                        get_fqfield("committee/5914213969/meeting_ids"): 1
                    },
                },
            ],
        )

    def test_perform_no_permission_1(self) -> None:
        with self.assertRaises(PermissionDenied):
            self.action.perform(self.valid_payload_1, user_id=4796568680)


class MeetingCreateActionWSGITester(BaseMeetingCreateActionTester):
    def setUp(self) -> None:
        super().setUp()
        self.user_id = (
            7121641734  # This user has perm MEETING_CAN_MANAGE for some committees.
        )
        self.application = create_test_application(user_id=self.user_id)

    def test_wsgi_request_empty(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.post(
            "/system/api/actions", json=[{"action": "meeting.create", "data": [{}]}]
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "data[0] must contain [\\'committee_id\\', \\'title\\'] properties",
            str(response.data),
        )

    def test_wsgi_request_fuzzy(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.post(
            "/system/api/actions",
            json=[
                {
                    "action": "meeting.create",
                    "data": [{"wrong_field": "text_AefohteiF8"}],
                }
            ],
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "data[0] must contain [\\'committee_id\\', \\'title\\'] properties",
            str(response.data),
        )

    def test_wsgi_request_correct_1(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.post(
            "/system/api/actions",
            json=[{"action": "meeting.create", "data": self.valid_payload_1}],
        )
        self.assertEqual(response.status_code, 200)
