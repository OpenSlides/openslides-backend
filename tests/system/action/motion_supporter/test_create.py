from typing import Any

from openslides_backend.action.mixins.delegation_based_restriction_mixin import (
    DelegationBasedRestriction,
)
from openslides_backend.permissions.base_classes import Permission
from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionSupporterCreateActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "motion/1": {
                "title": "motion_1",
                "meeting_id": 1,
                "state_id": 1,
                "supporter_ids": [],
            },
            "meeting/1": {
                "name": "name_meeting_1",
                "motion_ids": [1],
                "motions_supporters_min_amount": 1,
                "is_active_in_organization_id": 1,
                "committee_id": 60,
            },
            "motion_state/1": {
                "name": "state_1",
                "allow_support": True,
                "motion_ids": [1],
                "meeting_id": 1,
            },
            "committee/60": {"meeting_ids": [1]},
        }

    def create_delegator_test_data(
        self,
        is_delegator: bool = False,
        perm: Permission = Permissions.Motion.CAN_SUPPORT,
        delegator_setting: DelegationBasedRestriction = "users_forbid_delegator_as_supporter",
        disable_delegations: bool = False,
    ) -> None:
        self.create_meeting(1)
        self.set_models(
            {
                "motion/1": {
                    "title": "motion_1",
                    "meeting_id": 1,
                    "state_id": 1,
                    "supporter_ids": [],
                },
                "motion_state/1": {
                    "name": "state_1",
                    "allow_support": True,
                    "motion_ids": [1],
                    "meeting_id": 1,
                },
                "user/1": {"meeting_user_ids": [1]},
                "meeting_user/1": {"user_id": 1, "meeting_id": 1},
                "meeting/1": {
                    "name": "name_meeting_1",
                    "motion_ids": [1],
                    "motions_supporters_min_amount": 1,
                    "is_active_in_organization_id": 1,
                    "meeting_user_ids": [1],
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
            self.set_models(
                {
                    "meeting_user/1": {"vote_delegated_to_id": 2},
                    "meeting_user/2": {"vote_delegations_from_ids": [1]},
                }
            )
        self.set_organization_management_level(None)
        self.set_group_permissions(1, [perm])
        self.set_user_groups(1, [1])

    def test_create_meeting_support_system_deactivated(self) -> None:
        self.create_meeting(1)
        self.set_user_groups(1, [3])
        self.set_group_permissions(3, [Permissions.Motion.CAN_MANAGE_METADATA])
        self.set_models(
            {
                "motion/1": {
                    "title": "motion_1",
                    "meeting_id": 1,
                    "state_id": 1,
                },
                "meeting/1": {
                    "name": "name_meeting_1",
                    "motion_ids": [1],
                    "motions_supporters_min_amount": 0,
                },
                "motion_state/1": {
                    "name": "state_1",
                    "allow_support": False,
                    "motion_ids": [1],
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "motion_supporter.create", {"motion_id": 1, "meeting_user_id": 1}
        )
        self.assert_status_code(response, 400)
        assert "Motion supporters system deactivated." in response.json.get(
            "message", ""
        )

    def test_create_state_doesnt_allow_support(self) -> None:
        self.create_meeting(1)
        self.set_user_groups(1, [3])
        self.set_group_permissions(3, [Permissions.Motion.CAN_SUPPORT])
        self.set_organization_management_level(None)
        self.set_models(
            {
                "motion/1": {
                    "title": "motion_1",
                    "meeting_id": 1,
                    "state_id": 1,
                },
                "meeting/1": {
                    "name": "name_meeting_1",
                    "motion_ids": [1],
                    "motions_supporters_min_amount": 1,
                },
                "motion_state/1": {
                    "name": "state_1",
                    "allow_support": False,
                    "motion_ids": [1],
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "motion_supporter.create", {"motion_id": 1, "meeting_user_id": 1}
        )
        self.assert_status_code(response, 400)
        assert "The state does not allow support." in response.json["message"]

    def test_create_state_doesnt_allow_support_meta_perm(self) -> None:
        self.create_meeting(1)
        self.set_user_groups(1, [3])
        self.set_group_permissions(3, [Permissions.Motion.CAN_MANAGE_METADATA])
        self.set_organization_management_level(None)
        self.create_user("bob", [3])
        self.set_models(
            {
                "motion/1": {
                    "title": "motion_1",
                    "meeting_id": 1,
                    "state_id": 1,
                },
                "meeting/1": {
                    "name": "name_meeting_1",
                    "motion_ids": [1],
                    "motions_supporters_min_amount": 1,
                },
                "motion_state/1": {
                    "name": "state_1",
                    "allow_support": False,
                    "motion_ids": [1],
                    "meeting_id": 1,
                },
            }
        )
        response = self.request_multi(
            "motion_supporter.create",
            [
                {"motion_id": 1, "meeting_user_id": 1},
                {"motion_id": 1, "meeting_user_id": 2},
            ],
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion_supporter/1",
            {"motion_id": 1, "meeting_user_id": 1, "meeting_id": 1},
        )
        self.assert_model_exists(
            "motion_supporter/2",
            {"motion_id": 1, "meeting_user_id": 2, "meeting_id": 1},
        )

    def test_create_support(self) -> None:
        self.create_meeting(1)
        self.set_user_groups(1, [3])
        self.set_group_permissions(3, [Permissions.Motion.CAN_SUPPORT])
        self.set_organization_management_level(None)
        self.set_models(
            {
                "motion/1": {
                    "title": "motion_1",
                    "meeting_id": 1,
                    "state_id": 1,
                    "supporter_ids": [],
                },
                "meeting/1": {
                    "name": "name_meeting_1",
                    "motion_ids": [1],
                    "motions_supporters_min_amount": 1,
                },
                "motion_state/1": {
                    "name": "state_1",
                    "allow_support": True,
                    "motion_ids": [1],
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "motion_supporter.create", {"motion_id": 1, "meeting_user_id": 1}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion/1")
        assert model.get("supporter_ids") == [1]
        self.assert_model_exists(
            "meeting_user/1",
            {"meeting_id": 1, "user_id": 1, "motion_supporter_ids": [1]},
        )
        self.assert_model_exists(
            "motion_supporter/1",
            {"motion_id": 1, "meeting_user_id": 1, "meeting_id": 1},
        )

    def test_create_no_permission(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion_supporter.create",
            {"motion_id": 1, "meeting_user_id": 1},
        )

    def test_create_permission(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion_supporter.create",
            {"motion_id": 1, "meeting_user_id": 1},
            Permissions.Motion.CAN_SUPPORT,
        )

    def test_create_permission_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            self.permission_test_models,
            "motion_supporter.create",
            {"motion_id": 1, "meeting_user_id": 1},
        )

    def test_create_delegator_setting(self) -> None:
        self.create_meeting(1)
        self.set_user_groups(1, [3])
        self.set_group_permissions(3, [Permissions.Motion.CAN_SUPPORT])
        self.set_organization_management_level(None)
        self.set_models(
            {
                "motion/1": {
                    "title": "motion_1",
                    "meeting_id": 1,
                    "state_id": 1,
                    "supporter_ids": [],
                },
                "meeting/1": {
                    "name": "name_meeting_1",
                    "motion_ids": [1],
                    "motions_supporters_min_amount": 1,
                    "is_active_in_organization_id": 1,
                    "users_forbid_delegator_as_submitter": True,
                    "users_enable_vote_delegations": True,
                },
                "motion_state/1": {
                    "name": "state_1",
                    "allow_support": True,
                    "motion_ids": [1],
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "motion_supporter.create", {"motion_id": 1, "meeting_user_id": 1}
        )
        self.assert_status_code(response, 200)

    def test_create_delegator_setting_with_no_delegation(self) -> None:
        self.create_delegator_test_data()
        response = self.request(
            "motion_supporter.create", {"motion_id": 1, "meeting_user_id": 1}
        )
        self.assert_status_code(response, 200)

    def test_create_delegator_setting_with_delegation(self) -> None:
        self.create_delegator_test_data(is_delegator=True)
        response = self.request(
            "motion_supporter.create", {"motion_id": 1, "meeting_user_id": 1}
        )
        self.assert_status_code(response, 403)
        assert (
            response.json["message"]
            == "You are not allowed to perform action motion_supporter.create. Missing Permission: motion.can_manage_metadata"
        )

    def test_create_delegator_setting_with_delegation_delegations_turned_off(
        self,
    ) -> None:
        self.create_delegator_test_data(is_delegator=True, disable_delegations=True)
        response = self.request(
            "motion_supporter.create", {"motion_id": 1, "meeting_user_id": 1}
        )
        self.assert_status_code(response, 200)

    def test_create_delegator_setting_with_motion_manager_delegation(
        self,
    ) -> None:
        self.create_delegator_test_data(
            is_delegator=True, perm=Permissions.Motion.CAN_MANAGE_METADATA
        )
        response = self.request(
            "motion_supporter.create", {"motion_id": 1, "meeting_user_id": 1}
        )
        self.assert_status_code(response, 200)

    def test_create_with_irrelevant_delegator_setting(self) -> None:
        self.create_delegator_test_data(
            is_delegator=True, delegator_setting="users_forbid_delegator_as_submitter"
        )
        response = self.request(
            "motion_supporter.create", {"motion_id": 1, "meeting_user_id": 1}
        )
        self.assert_status_code(response, 200)

    def test_create_meeting_support_system_deactivated_on_other(self) -> None:
        self.create_meeting(1)
        self.set_user_groups(1, [3])
        self.set_group_permissions(3, [Permissions.Motion.CAN_MANAGE_METADATA])
        self.create_user("bob", [3])
        self.set_models(
            {
                "motion/1": {
                    "title": "motion_1",
                    "meeting_id": 1,
                    "state_id": 1,
                },
                "meeting/1": {
                    "name": "name_meeting_1",
                    "motion_ids": [1],
                    "motions_supporters_min_amount": 0,
                },
                "motion_state/1": {
                    "name": "state_1",
                    "allow_support": False,
                    "motion_ids": [1],
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "motion_supporter.create", {"motion_id": 1, "meeting_user_id": 2}
        )
        self.assert_status_code(response, 400)
        assert "Motion supporters system deactivated." in response.json.get(
            "message", ""
        )

    def test_create_support_on_other_support_perm_error(self) -> None:
        self.create_meeting(1)
        self.set_user_groups(1, [3])
        self.set_group_permissions(3, [Permissions.Motion.CAN_SUPPORT])
        self.set_organization_management_level(None)
        self.create_user("bob", [3])
        self.set_models(
            {
                "motion/1": {
                    "title": "motion_1",
                    "meeting_id": 1,
                    "state_id": 1,
                    "supporter_ids": [],
                },
                "meeting/1": {
                    "name": "name_meeting_1",
                    "motion_ids": [1],
                    "motions_supporters_min_amount": 1,
                },
                "motion_state/1": {
                    "name": "state_1",
                    "allow_support": True,
                    "motion_ids": [1],
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "motion_supporter.create", {"motion_id": 1, "meeting_user_id": 2}
        )
        self.assert_status_code(response, 403)
        assert (
            "You are not allowed to perform action motion_supporter.create. Missing Permission: motion.can_manage_metadata"
            in response.json.get("message", "")
        )

    def test_create_support_on_other(self) -> None:
        self.create_meeting(1)
        self.set_user_groups(1, [3])
        self.set_group_permissions(3, [Permissions.Motion.CAN_MANAGE_METADATA])
        self.set_organization_management_level(None)
        self.create_user("bob", [3])
        self.set_models(
            {
                "motion/1": {
                    "title": "motion_1",
                    "meeting_id": 1,
                    "state_id": 1,
                    "supporter_ids": [],
                },
                "meeting/1": {
                    "name": "name_meeting_1",
                    "motion_ids": [1],
                    "motions_supporters_min_amount": 1,
                },
                "motion_state/1": {
                    "name": "state_1",
                    "allow_support": True,
                    "motion_ids": [1],
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "motion_supporter.create", {"motion_id": 1, "meeting_user_id": 2}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion_supporter/1",
            {"motion_id": 1, "meeting_user_id": 2, "meeting_id": 1},
        )

    def test_create_delegator_setting_with_delegation_on_other(self) -> None:
        self.create_delegator_test_data(is_delegator=True)
        self.set_group_permissions(3, [Permissions.Motion.CAN_MANAGE_METADATA])
        self.set_organization_management_level(None)
        bob_id = self.create_user("bob", [1])
        self.login(bob_id)
        response = self.request(
            "motion_supporter.create", {"motion_id": 1, "meeting_user_id": 1}
        )
        self.assert_status_code(response, 403)
        assert (
            response.json["message"]
            == "You are not allowed to perform action motion_supporter.create. Missing Permission: motion.can_manage_metadata"
        )

    def test_create_delegator_setting_with_motion_manager_delegation_on_other(
        self,
    ) -> None:
        self.create_delegator_test_data(
            is_delegator=True, perm=Permissions.Motion.CAN_MANAGE_METADATA
        )
        self.set_group_permissions(3, [Permissions.Motion.CAN_MANAGE_METADATA])
        self.set_organization_management_level(None)
        bob_id = self.create_user("bob", [1])
        self.login(bob_id)
        response = self.request(
            "motion_supporter.create", {"motion_id": 1, "meeting_user_id": 1}
        )
        self.assert_status_code(response, 200)

    def test_create_duplicate_supporter(self) -> None:
        self.create_meeting(1)
        self.create_user("bob", [1])
        self.set_models(
            {
                "meeting_user/1": {
                    "motion_supporter_ids": [1],
                },
                "motion_supporter/1": {
                    "meeting_id": 1,
                    "motion_id": 1,
                    "meeting_user_id": 1,
                },
                "motion/1": {
                    "title": "motion_1",
                    "meeting_id": 1,
                    "state_id": 1,
                    "supporter_ids": [1],
                },
                "meeting/1": {
                    "name": "name_meeting_1",
                    "motion_ids": [1],
                    "motions_supporters_min_amount": 1,
                    "motion_supporter_ids": [1],
                },
                "motion_state/1": {
                    "name": "state_1",
                    "allow_support": True,
                    "motion_ids": [1],
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "motion_supporter.create", {"motion_id": 1, "meeting_user_id": 1}
        )
        self.assert_status_code(response, 400)
        assert "(meeting_user_id, motion_id) must be unique." in response.json.get(
            "message", ""
        )

    def test_create_duplicate_supporters(self) -> None:
        self.create_meeting(1)
        self.create_user("bob", [1])
        self.set_models(
            {
                "motion/1": {
                    "title": "motion_1",
                    "meeting_id": 1,
                    "state_id": 1,
                },
                "meeting/1": {
                    "name": "name_meeting_1",
                    "motion_ids": [1],
                    "motions_supporters_min_amount": 1,
                },
                "motion_state/1": {
                    "name": "state_1",
                    "allow_support": True,
                    "motion_ids": [1],
                    "meeting_id": 1,
                },
            }
        )
        response = self.request_multi(
            "motion_supporter.create",
            [
                {"motion_id": 1, "meeting_user_id": 1},
                {"motion_id": 1, "meeting_user_id": 1},
            ],
        )
        self.assert_status_code(response, 400)
        assert "(meeting_user_id, motion_id) must be unique." in response.json.get(
            "message", ""
        )
