from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from tests.system.action.base import BaseActionTestCase


class IdmConditionDeleteActionTest(BaseActionTestCase):
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

    def test_delete(self) -> None:
        response = self.request("idm_condition.delete", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("idm_condition/1")

    def test_delete_as_orga_admin(self) -> None:
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION, 1
        )
        response = self.request("idm_condition.delete", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("idm_condition/1")

    def test_delete_as_account_admin(self) -> None:
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_USERS, 1
        )
        response = self.request("idm_condition.delete", {"id": 1})
        self.assert_status_code(response, 403)
        assert (
            response.json["message"]
            == "You are not allowed to perform action idm_condition.delete. Missing OrganizationManagementLevel: can_manage_organization"
        )
        self.assert_model_exists("idm_condition/1")
