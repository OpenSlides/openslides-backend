from typing import Any

from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID
from tests.system.action.base import BaseActionTestCase


class GenderCreateActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.test_models: dict[str, dict[str, Any]] = {
            ONE_ORGANIZATION_FQID: {"name": "test_organization1"},
            "user/20": {"username": "test_user20"},
        }

    def test_create(self) -> None:
        self.set_models(self.test_models)
        self.set_models({"gender/1": {"organization_id": 1, "name": "male"}})
        gender_name = "female"

        response = self.request(
            "gender.create",
            {
                "name": gender_name,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "gender/1",
            {
                "name": "male",
                "organization_id": 1,
            },
        )
        self.assert_model_exists(
            "gender/2",
            {
                "name": gender_name,
                "organization_id": 1,
            },
        )

    def test_create_wrong_field(self) -> None:
        response = self.request(
            "gender.create",
            {
                "name": "test_gender_name",
                "wrong_field": "test",
            },
        )

        self.assert_status_code(response, 400)
        self.assertIn(
            "data must not contain {'wrong_field'} properties",
            response.json["message"],
        )
        self.assert_model_not_exists("gender/1")

    def test_create_existing_field(self) -> None:
        self.set_models({"gender/1": {"name": "exists"}})
        response = self.request(
            "gender.create",
            {
                "name": "exists",
            },
        )

        self.assert_status_code(response, 400)
        self.assertIn(
            "Gender 'exists' already exists.",
            response.json["message"],
        )
        self.assert_model_exists("gender/1")
        self.assert_model_not_exists("gender/2")

    def test_create_empty_data(self) -> None:
        response = self.request("gender.create", {})
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain ['name'] properties",
            response.json["message"],
        )
        self.assert_model_not_exists("gender/1")

    def test_create_empty_data_list(self) -> None:
        response = self.request_multi("gender.create", [])
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("gender/1")

    def test_create_empty_name(self) -> None:
        response = self.request("gender.create", {"name": ""})
        self.assert_status_code(response, 400)
        self.assertIn(
            "Empty gender name not allowed.",
            response.json["message"],
        )
        self.assert_model_not_exists("gender/1")

    def test_permission(self) -> None:
        self.base_permission_test(
            {},
            "gender.create",
            {
                "name": "test_Xcdfgee",
            },
            OrganizationManagementLevel.CAN_MANAGE_USERS,
        )

    def test_no_permission(self) -> None:
        self.base_permission_test(
            {},
            "gender.create",
            {
                "name": "test_Xcdfghee",
            },
        )
