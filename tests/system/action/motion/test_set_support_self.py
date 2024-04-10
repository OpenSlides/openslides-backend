from typing import Any

from openslides_backend.action.actions.user.delegation_based_restriction_mixin import (
    DelegationBasedRestriction,
)
from openslides_backend.permissions.base_classes import Permission
from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionSetSupportSelfActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "motion/1": {
                "title": "motion_1",
                "meeting_id": 1,
                "state_id": 1,
                "supporter_meeting_user_ids": [],
            },
            "meeting/1": {
                "name": "name_meeting_1",
                "motion_ids": [1],
                "motions_supporters_min_amount": 1,
                "is_active_in_organization_id": 1,
            },
            "motion_state/1": {
                "name": "state_1",
                "allow_support": True,
                "motion_ids": [1],
                "meeting_id": 1,
            },
        }

    def test_meeting_support_system_deactivated(self) -> None:
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
                    "is_active_in_organization_id": 1,
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
            "motion.set_support_self", {"motion_id": 1, "support": True}
        )
        self.assert_status_code(response, 400)
        assert "Motion supporters system deactivated." in response.json.get(
            "message", ""
        )

    def test_state_doesnt_allow_support(self) -> None:
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
                    "is_active_in_organization_id": 1,
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
            "motion.set_support_self", {"motion_id": 1, "support": True}
        )
        self.assert_status_code(response, 400)
        assert "The state does not allow support." in response.json["message"]

    def test_support(self) -> None:
        self.set_models(
            {
                "motion/1": {
                    "title": "motion_1",
                    "meeting_id": 1,
                    "state_id": 1,
                    "supporter_meeting_user_ids": [],
                },
                "meeting/1": {
                    "name": "name_meeting_1",
                    "motion_ids": [1],
                    "motions_supporters_min_amount": 1,
                    "is_active_in_organization_id": 1,
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
            "motion.set_support_self", {"motion_id": 1, "support": True}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion/1")
        assert model.get("supporter_meeting_user_ids") == [1]
        self.assert_model_exists(
            "meeting_user/1",
            {"meeting_id": 1, "user_id": 1, "supported_motion_ids": [1]},
        )

    def test_unsupport(self) -> None:
        self.set_models(
            {
                "meeting_user/1": {
                    "meeting_id": 1,
                    "user_id": 1,
                    "supported_motion_ids": [1],
                },
                "motion/1": {
                    "title": "motion_1",
                    "meeting_id": 1,
                    "state_id": 1,
                    "supporter_meeting_user_ids": [1],
                },
                "meeting/1": {
                    "name": "name_meeting_1",
                    "motion_ids": [1],
                    "motions_supporters_min_amount": 1,
                    "is_active_in_organization_id": 1,
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
            "motion.set_support_self", {"motion_id": 1, "support": False}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion/1")
        assert model.get("supporter_meeting_user_ids") == []
        self.assert_model_exists("meeting_user/1", {"supported_motion_ids": []})

    def test_unsupport_no_change(self) -> None:
        self.set_models(
            {
                "motion/1": {
                    "title": "motion_1",
                    "meeting_id": 1,
                    "state_id": 1,
                    "supporter_meeting_user_ids": [],
                },
                "meeting/1": {
                    "name": "name_meeting_1",
                    "motion_ids": [1],
                    "motions_supporters_min_amount": 1,
                    "is_active_in_organization_id": 1,
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
            "motion.set_support_self", {"motion_id": 1, "support": False}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion/1")
        assert model.get("supporter_meeting_user_ids") == []

    def test_set_support_self_no_permission(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion.set_support_self",
            {"motion_id": 1, "support": True},
        )

    def test_set_support_self_permission(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion.set_support_self",
            {"motion_id": 1, "support": True},
            Permissions.Motion.CAN_SUPPORT,
        )

    def create_delegator_test_data(
        self,
        is_delegator: bool = False,
        perm: Permission = Permissions.Motion.CAN_SUPPORT,
        delegator_setting: DelegationBasedRestriction = "users_forbid_delegator_as_supporter",
    ) -> None:
        self.create_meeting(1)
        self.set_models(
            {
                "motion/1": {
                    "title": "motion_1",
                    "meeting_id": 1,
                    "state_id": 1,
                    "supporter_meeting_user_ids": [],
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

    def test_delegator_setting(self) -> None:
        self.set_models(
            {
                "motion/1": {
                    "title": "motion_1",
                    "meeting_id": 1,
                    "state_id": 1,
                    "supporter_meeting_user_ids": [],
                },
                "meeting/1": {
                    "name": "name_meeting_1",
                    "motion_ids": [1],
                    "motions_supporters_min_amount": 1,
                    "is_active_in_organization_id": 1,
                    "users_forbid_delegator_as_submitter": True,
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
            "motion.set_support_self", {"motion_id": 1, "support": True}
        )
        self.assert_status_code(response, 200)

    def test_delegator_setting_with_no_delegation(self) -> None:
        self.create_delegator_test_data()
        response = self.request(
            "motion.set_support_self", {"motion_id": 1, "support": True}
        )
        self.assert_status_code(response, 200)

    def test_delegator_setting_with_delegation(self) -> None:
        self.create_delegator_test_data(is_delegator=True)
        response = self.request(
            "motion.set_support_self", {"motion_id": 1, "support": True}
        )
        self.assert_status_code(response, 403)
        assert (
            response.json["message"]
            == "You are not allowed to perform action motion.set_support_self. Missing Permission: motion.can_manage"
        )

    def test_delegator_setting_with_motion_manager_delegation(
        self,
    ) -> None:
        self.create_delegator_test_data(
            is_delegator=True, perm=Permissions.Motion.CAN_MANAGE
        )
        response = self.request(
            "motion.set_support_self", {"motion_id": 1, "support": True}
        )
        self.assert_status_code(response, 200)

    def test_with_irrelevant_delegator_setting(self) -> None:
        self.create_delegator_test_data(
            is_delegator=True, delegator_setting="users_forbid_delegator_as_submitter"
        )
        response = self.request(
            "motion.set_support_self", {"motion_id": 1, "support": True}
        )
        self.assert_status_code(response, 200)
