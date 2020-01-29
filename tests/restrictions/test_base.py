import json
from unittest import TestCase
from unittest.mock import MagicMock

from openslides_backend.restrictions import RestrictionBlob
from openslides_backend.restrictions.restrictions import RestrictionsHandler
from openslides_backend.shared.exceptions import RestrictionException
from openslides_backend.shared.patterns import KEYSEPARATOR

from ..utils import Client, ResponseWrapper, create_test_application, get_fqfield


class RestrictionsBaseUnitTester(TestCase):
    def setUp(self) -> None:
        self.restrictions_handler = RestrictionsHandler()
        self.user_id = 0

    def test_with_bad_key(self) -> None:
        payload = [
            RestrictionBlob(
                user_id=self.user_id, fqfields=["0rg4n12a710n/1/committee_ids"]
            )
        ]
        with self.assertRaises(RestrictionException) as context_manager:
            self.restrictions_handler.handle_request(
                payload=payload, logging=MagicMock(), services=MagicMock(),
            )
        self.assertEqual(
            context_manager.exception.message,
            f"data[0].fqfields[0] must match pattern ^[a-z_]+{KEYSEPARATOR}[1-9]\\d*{KEYSEPARATOR}[a-z_]+$",
        )

    def test_restrictions_handler(self) -> None:
        payload = [
            RestrictionBlob(
                user_id=self.user_id, fqfields=["organisation/1/committee_ids"]
            )
        ]
        response = self.restrictions_handler.handle_request(
            payload=payload, logging=MagicMock(), services=MagicMock(),
        )
        # expected = {get_fqfield("organisation/1/committee_ids"): [5914213969]}
        expected = [
            {
                get_fqfield(
                    "organisation/1/committee_ids"
                ): "This is a restricted field content made by dummy restrictor."
            }
        ]
        self.assertEqual(response, expected)


class RestrictionBaseWSGITester(TestCase):
    def setUp(self) -> None:
        self.user_id = 0
        self.application = create_test_application(
            user_id=self.user_id, view_name="RestrictionsView"
        )

    def test_wsgi_request_empty(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.get("/", json=[{"user_id": self.user_id, "fqfields": []}])
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "data[0].fqfields must contain at least 1 items", str(response.data),
        )

    def test_wsgi_request_fuzzy(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.get(
            "/",
            json=[{"user_id": self.user_id, "fqfields": ["0rg4n12a710n/1/bad_field"]}],
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            f"data[0].fqfields[0] must match pattern ^[a-z_]+{KEYSEPARATOR}[1-9]\\\\d*{KEYSEPARATOR}[a-z_]+$",
            str(response.data),
        )

    def test_wsgi_request_correct_1(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.get(
            "/",
            json=[
                {"user_id": self.user_id, "fqfields": ["organisation/1/committee_ids"]}
            ],
        )
        self.assertEqual(response.status_code, 200)
        # expected = {"organisation/1/committee_ids": [5914213969]}
        expected = [
            {
                "organisation/1/committee_ids": "This is a restricted field content made by dummy restrictor."
            }
        ]
        self.assertEqual(json.loads(response.data), expected)
