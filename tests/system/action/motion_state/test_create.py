from typing import Any

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionStateActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "motion_workflow/42": {
                "name": "test_name_fjwnq8d8tje8",
                "meeting_id": 1,
            },
        }

    def test_create(self) -> None:
        self.set_models(
            {
                "meeting/1": {"is_active_in_organization_id": 1, "committee_id": 1},
                "motion_workflow/42": {
                    "name": "test_name_fjwnq8d8tje8",
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "motion_state.create",
            {
                "name": "test_Xcdfgee",
                "workflow_id": 42,
                "allow_motion_forwarding": True,
                "set_workflow_timestamp": True,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion_state/1")
        model = self.get_model("motion_state/1")
        assert model.get("name") == "test_Xcdfgee"
        assert model.get("restrictions") == []
        assert model.get("merge_amendment_into_final") == "undefined"
        assert model.get("css_class") == "lightblue"
        assert model.get("allow_motion_forwarding") is True
        assert model.get("set_workflow_timestamp") is True

    def test_create_as_new_first_state(self) -> None:
        self.set_models(
            {
                "meeting/1": {"is_active_in_organization_id": 1, "committee_id": 1},
                "motion_workflow/42": {
                    "name": "test_name_fjwnq8d8tje8",
                    "meeting_id": 1,
                    "first_state_id": 1,
                },
                "motion_state/1": {
                    "workflow_id": 42,
                    "first_state_of_workflow_id": 42,
                    "name": "first state one",
                },
            }
        )
        response = self.request_json(
            [
                {
                    "action": "motion_state.create",
                    "data": [
                        {
                            "name": "first state two",
                            "workflow_id": 42,
                            "first_state_of_workflow_id": 42,
                        }
                    ],
                }
            ]
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "There is already a first state for this workflow set. You can't change it.",
            response.json["message"],
        )

    def test_create_as_new_first_state_of_second_workflow(self) -> None:
        self.set_models(
            {
                "meeting/1": {"is_active_in_organization_id": 1, "committee_id": 1},
                "motion_workflow/42": {
                    "name": "test_name_42",
                    "meeting_id": 1,
                    "first_state_id": 1,
                },
                "motion_state/1": {
                    "workflow_id": 42,
                    "first_state_of_workflow_id": 42,
                    "name": "first state one",
                },
                "motion_workflow/43": {
                    "name": "test_name_43",
                    "meeting_id": 1,
                    "first_state_id": 2,
                },
                "motion_state/2": {
                    "workflow_id": 43,
                    "first_state_of_workflow_id": 43,
                    "name": "first state two",
                },
            }
        )
        response = self.request_json(
            [
                {
                    "action": "motion_state.create",
                    "data": [
                        {
                            "name": "first state three",
                            "workflow_id": 42,
                            "first_state_of_workflow_id": 43,
                        }
                    ],
                }
            ]
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "This state of workflow 42 cannot be the first state of workflow 43.",
            response.json["message"],
        )

    def test_create_enum_fields(self) -> None:
        self.set_models(
            {
                "meeting/1": {"is_active_in_organization_id": 1, "committee_id": 1},
                "motion_workflow/42": {
                    "name": "test_name_fjwnq8d8tje8",
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "motion_state.create",
            {
                "name": "test_Xcdfgee",
                "workflow_id": 42,
                "css_class": "red",
                "restrictions": ["is_submitter"],
                "merge_amendment_into_final": "do_not_merge",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion_state/1")
        model = self.get_model("motion_state/1")
        assert model.get("name") == "test_Xcdfgee"
        assert model.get("workflow_id") == 42
        assert model.get("css_class") == "red"
        assert model.get("restrictions") == ["is_submitter"]
        assert model.get("merge_amendment_into_final") == "do_not_merge"

    def test_create_auto_weight(self) -> None:
        self.set_models(
            {
                "meeting/1": {"is_active_in_organization_id": 1, "committee_id": 1},
                "motion_workflow/42": {
                    "name": "test_name_fjwnq8d8tje8",
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "motion_state.create",
            {
                "name": "test_Xcdfgee",
                "workflow_id": 42,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion_state/1", {"weight": 1})
        response = self.request(
            "motion_state.create",
            {
                "name": "test_Xcdfgee",
                "workflow_id": 42,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion_state/2", {"weight": 2})

    def test_create_manual_weight(self) -> None:
        self.set_models(
            {
                "meeting/1": {"is_active_in_organization_id": 1, "committee_id": 1},
                "motion_workflow/42": {
                    "name": "test_name_fjwnq8d8tje8",
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "motion_state.create",
            {
                "name": "test_Xcdfgee",
                "workflow_id": 42,
                "weight": 42,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion_state/1", {"weight": 42})

    def test_create_empty_data(self) -> None:
        response = self.request("motion_state.create", {})
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain ['name', 'workflow_id'] properties",
            response.json["message"],
        )

    def test_create_wrong_field(self) -> None:
        response = self.request(
            "motion_state.create", {"wrong_field": "text_AefohteiF8"}
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain ['name', 'workflow_id'] properties",
            response.json["message"],
        )

    def test_create_forbidden_value_1(self) -> None:
        response = self.request(
            "motion_state.create",
            {"name": "test_Xcdfgee", "workflow_id": 42, "css_class": "pink"},
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data.css_class must be one of ['grey', 'red', 'green', 'lightblue', 'yellow']",
            response.json["message"],
        )

    def test_create_forbidden_value_2(self) -> None:
        response = self.request(
            "motion_state.create",
            {
                "name": "test_Xcdfgee",
                "workflow_id": 42,
                "restrictions": ["is__XXXX__submitter"],
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data.restrictions[0] must be one of ['motion.can_see_internal', 'motion.can_manage_metadata', 'motion.can_manage', 'is_submitter']",
            response.json["message"],
        )

    def test_create_no_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion_state.create",
            {"name": "test_Xcdfgee", "workflow_id": 42},
        )

    def test_create_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion_state.create",
            {"name": "test_Xcdfgee", "workflow_id": 42},
            Permissions.Motion.CAN_MANAGE,
        )

    def test_create_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            self.permission_test_models,
            "motion_state.create",
            {"name": "test_Xcdfgee", "workflow_id": 42},
        )
