from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from tests.system.action.base import BaseActionTestCase


class IdmConditionUpdateActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.set_models(
            {
                "idm_mapper/1": {"group_external_ids": ["AAAAAAAaaaaaaaa"]},
                "idm_condition/1": {
                    "idm_field": "ew_its_a_field",
                    "regex": "[a]*",
                    "mapper_id": 1,
                },
            }
        )

    def test_update(self) -> None:
        response = self.request(
            "idm_condition.update", {"id": 1, "idm_field": "go_away", "regex": ".*"}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "idm_condition/1", {"idm_field": "go_away", "regex": ".*"}
        )

    def test_update_missing_idm_field(self) -> None:
        response = self.request("idm_condition.update", {"id": 1, "regex": ".*"})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "idm_condition/1", {"idm_field": "ew_its_a_field", "regex": ".*"}
        )

    def test_update_missing_regex(self) -> None:
        response = self.request(
            "idm_condition.update", {"id": 1, "idm_field": "go_away"}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "idm_condition/1", {"idm_field": "go_away", "regex": "[a]*"}
        )

    def test_update_as_orga_admin(self) -> None:
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION, 1
        )
        response = self.request(
            "idm_condition.update", {"id": 1, "idm_field": "go_away", "regex": ".*"}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "idm_condition/1", {"idm_field": "go_away", "regex": ".*"}
        )

    def test_update_as_account_admin(self) -> None:
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_USERS, 1
        )
        response = self.request(
            "idm_condition.update", {"id": 1, "idm_field": "go_away", "regex": ".*"}
        )
        self.assert_status_code(response, 403)
        assert (
            response.json["message"]
            == "You are not allowed to perform action idm_condition.update. Missing OrganizationManagementLevel: can_manage_organization"
        )
