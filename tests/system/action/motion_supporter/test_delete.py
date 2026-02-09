from typing import Any

from openslides_backend.action.mixins.delegation_based_restriction_mixin import (
    DelegationBasedRestriction,
)
from openslides_backend.permissions.base_classes import Permission
from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionSupporterDeleteActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting(meeting_data={"motions_supporters_min_amount": 1})
        self.create_motion(1, 1)
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "meeting_user/1": {
                "meeting_id": 1,
                "user_id": 2,
            },
            "group/1": {"meeting_user_ids": [1]},
            "motion_supporter/2": {
                "meeting_user_id": 1,
                "motion_id": 1,
                "meeting_id": 1,
            },
            "motion_state/1": {"allow_support": True},
        }

    def create_delegator_test_data(
        self,
        is_delegator: bool = False,
        perm: Permission = Permissions.Motion.CAN_SUPPORT,
        delegator_setting: DelegationBasedRestriction = "users_forbid_delegator_as_supporter",
        disable_delegations: bool = False,
    ) -> None:
        self.set_user_groups(1, [1])
        self.set_models(
            {
                "motion_supporter/2": {
                    "meeting_user_id": 1,
                    "motion_id": 1,
                    "meeting_id": 1,
                },
                "motion_state/1": {"allow_support": True},
                "meeting/1": {
                    **(
                        {}
                        if disable_delegations
                        else {"users_enable_vote_delegations": True}
                    ),
                    delegator_setting: True,
                },
            }
        )
        if is_delegator:
            self.create_user("delegatee", [1])
            self.set_models({"meeting_user/1": {"vote_delegated_to_id": 2}})
        self.set_organization_management_level(None)
        self.set_group_permissions(1, [perm])

    def test_delete_meeting_support_system_deactivated(self) -> None:
        self.set_user_groups(1, [3])
        self.set_group_permissions(3, [Permissions.Motion.CAN_MANAGE_METADATA])
        self.set_models(
            {
                "motion_supporter/2": {
                    "motion_id": 1,
                    "meeting_id": 1,
                    "meeting_id": 1,
                },
                "meeting/1": {"motions_supporters_min_amount": 0},
                "motion_state/1": {"allow_support": False},
            }
        )
        response = self.request("motion_supporter.delete", {"id": 2})
        self.assert_status_code(response, 400)
        self.assertEqual(
            "Motion supporters system deactivated.", response.json.get("message", "")
        )

    def test_delete_state_doesnt_allow_support(self) -> None:
        self.set_user_groups(1, [3])
        self.set_group_permissions(3, [Permissions.Motion.CAN_SUPPORT])
        self.set_organization_management_level(None)
        self.set_models(
            {
                "motion_supporter/2": {
                    "motion_id": 1,
                    "meeting_id": 1,
                    "meeting_user_id": 1,
                },
                "motion_state/1": {"allow_support": False},
            }
        )
        response = self.request("motion_supporter.delete", {"id": 2})
        self.assert_status_code(response, 400)
        self.assertEqual("The state does not allow support.", response.json["message"])

    def test_delete_state_doesnt_allow_support_meta_perm(self) -> None:
        self.set_user_groups(1, [3])
        self.set_group_permissions(3, [Permissions.Motion.CAN_MANAGE_METADATA])
        self.set_organization_management_level(None)
        self.set_models(
            {
                "motion_supporter/2": {"motion_id": 1, "meeting_id": 1},
                "motion_state/1": {"allow_support": False},
            }
        )
        response = self.request("motion_supporter.delete", {"id": 2})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("motion_supporter/2")

    def test_delete_unsupport(self) -> None:
        self.set_user_groups(1, [3])
        self.set_group_permissions(3, [Permissions.Motion.CAN_SUPPORT])
        self.set_organization_management_level(None)
        self.set_models(
            {
                "motion_supporter/2": {
                    "meeting_user_id": 1,
                    "motion_id": 1,
                    "meeting_id": 1,
                },
                "motion_state/1": {"allow_support": True},
            }
        )
        response = self.request("motion_supporter.delete", {"id": 2})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("motion_supporter/2")
        self.assert_model_exists("meeting_user/1")
        self.assert_model_exists("motion/1")

    def test_delete_no_permission(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion_supporter.delete",
            {"id": 2},
        )

    def test_delete_permission(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion_supporter.delete",
            {"id": 2},
            Permissions.Motion.CAN_SUPPORT,
        )

    def test_delete_permission_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            self.permission_test_models,
            "motion_supporter.delete",
            {"id": 2},
        )

    def test_delete_delegator_setting(self) -> None:
        self.set_user_groups(1, [3])
        self.set_models(
            {
                "motion_supporter/2": {
                    "meeting_user_id": 1,
                    "motion_id": 1,
                    "meeting_id": 1,
                },
                "meeting/1": {
                    "users_forbid_delegator_as_submitter": True,
                    "users_enable_vote_delegations": True,
                },
                "motion_state/1": {"allow_support": True},
            }
        )
        response = self.request("motion_supporter.delete", {"id": 2})
        self.assert_status_code(response, 200)

    def test_delete_delegator_setting_with_no_delegation(self) -> None:
        self.create_delegator_test_data()
        response = self.request("motion_supporter.delete", {"id": 2})
        self.assert_status_code(response, 200)

    def test_delete_delegator_setting_with_delegation(self) -> None:
        self.create_delegator_test_data(is_delegator=True)
        response = self.request("motion_supporter.delete", {"id": 2})
        self.assert_status_code(response, 403)
        assert (
            response.json["message"]
            == "You are not allowed to perform action motion_supporter.delete. Missing Permission: motion.can_manage_metadata"
        )

    def test_delete_delegator_setting_with_delegation_delegations_turned_off(
        self,
    ) -> None:
        self.create_delegator_test_data(is_delegator=True, disable_delegations=True)
        response = self.request("motion_supporter.delete", {"id": 2})
        self.assert_status_code(response, 200)

    def test_delete_delegator_setting_with_motion_manager_delegation(
        self,
    ) -> None:
        self.create_delegator_test_data(
            is_delegator=True, perm=Permissions.Motion.CAN_MANAGE_METADATA
        )
        response = self.request("motion_supporter.delete", {"id": 2})
        self.assert_status_code(response, 200)

    def test_delete_with_irrelevant_delegator_setting(self) -> None:
        self.create_delegator_test_data(
            is_delegator=True, delegator_setting="users_forbid_delegator_as_submitter"
        )
        response = self.request("motion_supporter.delete", {"id": 2})
        self.assert_status_code(response, 200)

    def test_delete_unsupport_on_other(self) -> None:
        self.set_user_groups(1, [3])
        self.set_group_permissions(3, [Permissions.Motion.CAN_MANAGE_METADATA])
        self.set_organization_management_level(None)
        self.create_user("bob", [3])
        self.set_models(
            {
                "motion_supporter/2": {
                    "meeting_user_id": 1,
                    "motion_id": 1,
                    "meeting_id": 1,
                },
                "motion_state/1": {"allow_support": True},
            }
        )
        response = self.request("motion_supporter.delete", {"id": 2})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("motion_supporter/2")
        self.assert_model_exists("meeting_user/1")
        self.assert_model_exists("motion/1")

    def test_delete_delegator_setting_with_delegation_on_other(self) -> None:
        self.create_delegator_test_data(is_delegator=True)
        self.set_group_permissions(3, [Permissions.Motion.CAN_MANAGE_METADATA])
        self.set_organization_management_level(None)
        bob_id = self.create_user("bob", [1])
        self.login(bob_id)
        response = self.request("motion_supporter.delete", {"id": 2})
        self.assert_status_code(response, 403)
        assert (
            response.json["message"]
            == "You are not allowed to perform action motion_supporter.delete. Missing Permission: motion.can_manage_metadata"
        )

    def test_delete_delegator_setting_with_motion_manager_delegation_on_other(
        self,
    ) -> None:
        self.create_delegator_test_data(
            is_delegator=True, perm=Permissions.Motion.CAN_MANAGE_METADATA
        )
        self.set_group_permissions(3, [Permissions.Motion.CAN_MANAGE_METADATA])
        self.set_organization_management_level(None)
        bob_id = self.create_user("bob", [1])
        self.login(bob_id)
        response = self.request("motion_supporter.delete", {"id": 2})
        self.assert_status_code(response, 200)
