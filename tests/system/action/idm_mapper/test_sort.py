from typing import Any

from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from tests.system.action.base import BaseActionTestCase


class IdmMapperSortActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.test_models: dict[str, dict[str, Any]] = {
            "idm_mapper/31": {"group_external_ids": ["A"]},
            "idm_mapper/32": {"group_external_ids": ["B"]},
        }

    def test_sort_correct(self) -> None:
        self.create_meeting(222)
        self.set_models(self.test_models)
        response = self.request(
            "idm_mapper.sort",
            {"idm_mapper_ids": [32, 31]},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("idm_mapper/31", {"weight": 2})
        self.assert_model_exists("idm_mapper/32", {"weight": 1})

    def test_sort_missing_model(self) -> None:
        self.create_meeting(222)
        self.set_models(self.test_models)
        response = self.request(
            "idm_mapper.sort",
            {"idm_mapper_ids": [32, 31, 33]},
        )
        self.assert_status_code(response, 400)
        assert (
            "idm_mapper sorting failed, because element idm_mapper/33 doesn't exist."
            in response.json["message"]
        )

    def test_sort_one_model_too_few(self) -> None:
        self.create_meeting(222)
        self.set_models(self.test_models)
        response = self.request(
            "idm_mapper.sort",
            {"idm_mapper_ids": [32]},
        )
        self.assert_status_code(response, 400)
        assert (
            "idm_mapper sorting failed, because some elements were not included in the call."
            in response.json["message"]
        )

    def test_sort_no_permissions(self) -> None:
        self.base_permission_test(
            self.test_models,
            "idm_mapper.sort",
            {"idm_mapper_ids": [32, 31]},
        )

    def test_sort_permissions(self) -> None:
        self.base_permission_test(
            self.test_models,
            "idm_mapper.sort",
            {"idm_mapper_ids": [32, 31]},
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
        )
        self.assert_model_exists("idm_mapper/31", {"weight": 2})
        self.assert_model_exists("idm_mapper/32", {"weight": 1})
