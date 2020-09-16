from unittest.mock import MagicMock

import simplejson as json

from openslides_backend.action import ActionPayload
from openslides_backend.action.committee.create import CommitteeCreate
from openslides_backend.shared.exceptions import ActionException, PermissionDenied
from tests.system.action.base import BaseActionTestCase
from tests.util import get_fqfield, get_fqid

# TODO: remove this file once adapted to the new schema.


class BaseCommitteeCreateActionTester(BaseActionTestCase):
    """
    Tests the committee create action.
    """

    def setUp(self) -> None:
        self.valid_payload_1 = [{"organisation_id": 1, "name": "name_ieth5Ha1th"}]


class CommitteeCreateActionUnitTester(BaseCommitteeCreateActionTester):
    def setUp(self) -> None:
        super().setUp()
        user_id = 7668157706
        self.datastore_content = {
            get_fqfield("organisation/1/name"): "test_organisation_name",
            get_fqfield("organisation/1/committee_ids"): [5914213969],
        }
        self.action = CommitteeCreate(
            "committee.create",
            MagicMock(superuser=user_id),  # noqa: F821
            MagicMock(datastore_content=self.datastore_content),  # noqa: F821
        )
        self.action.user_id = user_id

    def test_validation_empty(self) -> None:
        payload: ActionPayload = []
        with self.assertRaises(ActionException):
            self.action.validate(payload)

    def test_validation_empty_2(self) -> None:
        payload: ActionPayload = [{}]
        with self.assertRaises(ActionException):
            self.action.validate(payload)

    def test_validation_fuzzy(self) -> None:
        payload = [{"wrong_field": "text_daiKeesh9o"}]
        with self.assertRaises(ActionException):
            self.action.validate(payload)

    def test_validation_correct_1(self) -> None:
        self.action.validate(self.valid_payload_1)

    def test_prepare_dataset_1(self) -> None:
        dataset = self.action.prepare_dataset(self.valid_payload_1)
        self.assertEqual(
            dataset["data"],
            [
                {
                    "instance": self.valid_payload_1[0],
                    "new_id": 42,
                    "relations": {
                        get_fqfield("organisation/1/committee_ids"): {
                            "type": "add",
                            "value": [5914213969, 42],
                        },
                    },
                }
            ],
        )


class CommitteeCreateActionPerformTester(BaseCommitteeCreateActionTester):
    def setUp(self) -> None:
        super().setUp()
        self.user_id = 7668157706
        self.datastore_content = {
            get_fqfield("organisation/1/name"): "test_organisation_name",
            get_fqfield("organisation/1/committee_ids"): [5914213969],
        }
        self.action = CommitteeCreate(
            "committee.create",
            MagicMock(superuser=self.user_id),  # noqa: F821
            MagicMock(datastore_content=self.datastore_content),  # noqa: F821
        )

    def test_perform_empty(self) -> None:
        payload: ActionPayload = []
        with self.assertRaises(ActionException):
            self.action.perform(payload, user_id=self.user_id)

    def test_perform_empty_2(self) -> None:
        payload: ActionPayload = [{}]
        with self.assertRaises(ActionException):
            self.action.perform(payload, user_id=self.user_id)

    def test_perform_fuzzy(self) -> None:
        payload = [{"wrong_field": "text_dio0ahP6Oo"}]
        with self.assertRaises(ActionException):
            self.action.perform(payload, user_id=self.user_id)

    def test_perform_correct_1(self) -> None:
        expected = [
            {
                "events": [
                    {
                        "type": "create",
                        "fqid": get_fqid("committee/42"),
                        "fields": {"organisation_id": 1, "name": "name_ieth5Ha1th"},
                    },
                    {
                        "type": "update",
                        "fqid": get_fqid("organisation/1"),
                        "fields": {"committee_ids": [5914213969, 42]},
                    },
                ],
                "information": {
                    get_fqid("committee/42"): ["Object created"],
                    get_fqid("organisation/1"): ["Object attached to committee"],
                },
                "user_id": self.user_id,
            },
        ]
        write_request_elements = self.action.perform(
            self.valid_payload_1, user_id=self.user_id
        )
        result = list(write_request_elements)
        self.assertEqual(result, expected)

    def test_perform_no_permission_1(self) -> None:
        with self.assertRaises(PermissionDenied):
            self.action.perform(self.valid_payload_1, user_id=4796568680)


class CommitteeCreateActionWSGITester(BaseCommitteeCreateActionTester):
    def setUp(self) -> None:
        super().setUp()
        self.datastore_content = {
            get_fqfield("organisation/1/name"): "test_organisation_name",
            get_fqfield("organisation/1/committee_ids"): [5914213969],
        }
        self.user_id = 7668157706

    def test_wsgi_request_empty(self) -> None:
        expected_write_data = ""  # noqa: F841
        response = self.client.post(
            "/", json=[{"action": "committee.create", "data": [{}]}]
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data[0] must contain [\\'organisation_id\\', \\'name\\'] properties",
            str(response.data),
        )

    def test_wsgi_request_fuzzy(self) -> None:
        expected_write_data = ""  # noqa: F841
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "committee.create",
                    "data": [{"wrong_field": "text_nobieH9ieS"}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data[0] must contain [\\'organisation_id\\', \\'name\\'] properties",
            str(response.data),
        )

    def test_wsgi_request_correct_1(self) -> None:
        expected_write_data = json.dumps(  # noqa: F841
            {
                "events": [
                    {
                        "type": "create",
                        "fqid": "committee/42",
                        "fields": {"organisation_id": 1, "name": "name_ieth5Ha1th"},
                    },
                    {
                        "type": "update",
                        "fqid": "organisation/1",
                        "fields": {"committee_ids": [5914213969, 42]},
                    },
                ],
                "information": {
                    "committee/42": ["Object created"],
                    "organisation/1": ["Object attached to committee"],
                },
                "user_id": self.user_id,
                "locked_fields": {"organisation/1": 1},
            }
        )
        response = self.client.post(
            "/", json=[{"action": "committee.create", "data": self.valid_payload_1}],
        )
        self.assert_status_code(response, 200)


class CommitteeCreateActionWSGITesterNoPermission(BaseCommitteeCreateActionTester):
    def setUp(self) -> None:
        super().setUp()
        self.datastore_content = {
            get_fqfield("organisation/1/name"): "test_organisation_name"
        }
        self.user_id_no_permission = 9707919439

    def test_wsgi_request_no_permission_1(self) -> None:
        expected_write_data = ""  # noqa: F841
        response = self.client.post(
            "/", json=[{"action": "committee.create", "data": self.valid_payload_1}],
        )
        self.assert_status_code(response, 403)
