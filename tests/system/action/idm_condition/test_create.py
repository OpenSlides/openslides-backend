from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from tests.system.action.base import BaseActionTestCase


class IdmConditionCreateActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.set_models({"idm_mapper/1": {"group_external_ids": ["AAAAAAAaaaaaaaa"]}})

    def test_create(self) -> None:
        response = self.request(
            "idm_condition.create",
            {"idm_field": "go_away", "regex": ".*", "mapper_id": 1},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "idm_condition/1", {"idm_field": "go_away", "regex": ".*", "mapper_id": 1}
        )

    def test_create_missing_idm_field(self) -> None:
        response = self.request("idm_condition.create", {"regex": ".*", "mapper_id": 1})
        self.assert_status_code(response, 400)
        assert (
            response.json["message"]
            == "Action idm_condition.create: data must contain ['idm_field'] properties"
        )

    def test_create_missing_regex(self) -> None:
        response = self.request(
            "idm_condition.create", {"idm_field": "go_away", "mapper_id": 1}
        )
        self.assert_status_code(response, 400)
        assert (
            response.json["message"]
            == "Action idm_condition.create: data must contain ['regex'] properties"
        )

    def test_create_missing_mapper_id(self) -> None:
        response = self.request(
            "idm_condition.create", {"idm_field": "go_away", "regex": ".*"}
        )
        self.assert_status_code(response, 400)
        assert (
            response.json["message"]
            == "Action idm_condition.create: data must contain ['mapper_id'] properties"
        )

    def test_create_idm_field_none(self) -> None:
        response = self.request(
            "idm_condition.create", {"idm_field": None, "regex": ".*", "mapper_id": 1}
        )
        self.assert_status_code(response, 400)
        assert (
            response.json["message"]
            == "Action idm_condition.create: data.idm_field must be string"
        )

    def test_create_nonexistant_mapper(self) -> None:
        response = self.request(
            "idm_condition.create",
            {"idm_field": "go_away", "regex": ".*", "mapper_id": 2},
        )
        self.assert_status_code(response, 400)
        assert response.json["message"] == "Model 'idm_mapper/2' does not exist."

    def test_create_as_orga_admin(self) -> None:
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION, 1
        )
        response = self.request(
            "idm_condition.create",
            {"idm_field": "go_away", "regex": ".*", "mapper_id": 1},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "idm_condition/1", {"idm_field": "go_away", "regex": ".*", "mapper_id": 1}
        )

    def test_create_as_account_admin(self) -> None:
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_USERS, 1
        )
        response = self.request(
            "idm_condition.create",
            {"idm_field": "go_away", "regex": ".*", "mapper_id": 1},
        )
        self.assert_status_code(response, 403)
        assert (
            response.json["message"]
            == "You are not allowed to perform action idm_condition.create. Missing OrganizationManagementLevel: can_manage_organization"
        )
