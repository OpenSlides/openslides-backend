from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionStateActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()

    def test_create(self) -> None:
        response = self.request(
            "motion_state.create",
            {
                "name": "test_Xcdfgee",
                "workflow_id": 1,
                "allow_motion_forwarding": True,
                "allow_amendment_forwarding": True,
                "set_workflow_timestamp": True,
                "state_button_label": "State button label",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion_state/2",
            {
                "name": "test_Xcdfgee",
                "restrictions": [],
                "merge_amendment_into_final": "undefined",
                "css_class": "lightblue",
                "allow_motion_forwarding": True,
                "allow_amendment_forwarding": True,
                "set_workflow_timestamp": True,
                "state_button_label": "State button label",
            },
        )

    def test_create_as_new_first_state(self) -> None:
        response = self.request_json(
            [
                {
                    "action": "motion_state.create",
                    "data": [
                        {
                            "name": "first state two",
                            "workflow_id": 1,
                            "first_state_of_workflow_id": 1,
                        }
                    ],
                }
            ]
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "There is already a first state for this workflow set. You can't change it.",
            response.json["message"],
        )

    def test_create_as_new_first_state_of_second_workflow(self) -> None:
        self.set_models(
            {
                "motion_workflow/43": {
                    "name": "test_name_43",
                    "meeting_id": 1,
                    "first_state_id": 2,
                },
                "motion_state/2": {
                    "meeting_id": 1,
                    "workflow_id": 43,
                    "first_state_of_workflow_id": 43,
                    "name": "first state two",
                    "weight": 2,
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
                            "workflow_id": 1,
                            "first_state_of_workflow_id": 43,
                        }
                    ],
                }
            ]
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "This state of workflow 1 cannot be the first state of workflow 43.",
            response.json["message"],
        )

    def test_create_enum_fields(self) -> None:
        response = self.request(
            "motion_state.create",
            {
                "name": "test_Xcdfgee",
                "workflow_id": 1,
                "css_class": "red",
                "restrictions": ["is_submitter"],
                "merge_amendment_into_final": "do_not_merge",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion_state/2")
        self.assert_model_exists(
            "motion_state/2",
            {
                "name": "test_Xcdfgee",
                "workflow_id": 1,
                "css_class": "red",
                "restrictions": ["is_submitter"],
                "merge_amendment_into_final": "do_not_merge",
            },
        )

    def test_create_auto_weight(self) -> None:
        response = self.request(
            "motion_state.create",
            {"name": "test_Xcdfgee", "workflow_id": 1},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion_state/2", {"weight": 37})

    def test_create_manual_weight(self) -> None:
        response = self.request(
            "motion_state.create",
            {"name": "test_Xcdfgee", "workflow_id": 1, "weight": 1},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion_state/2", {"weight": 1})

    def test_create_empty_data(self) -> None:
        response = self.request("motion_state.create", {})
        self.assert_status_code(response, 400)
        self.assertEqual(
            "Action motion_state.create: data must contain ['name', 'workflow_id'] properties",
            response.json["message"],
        )

    def test_create_wrong_field(self) -> None:
        response = self.request(
            "motion_state.create", {"wrong_field": "text_AefohteiF8"}
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "Action motion_state.create: data must contain ['name', 'workflow_id'] properties",
            response.json["message"],
        )

    def test_create_forbidden_value_1(self) -> None:
        response = self.request(
            "motion_state.create",
            {"name": "test_Xcdfgee", "workflow_id": 1, "css_class": "pink"},
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "Action motion_state.create: data.css_class must be one of ['grey', 'red', 'green', 'lightblue', 'yellow']",
            response.json["message"],
        )

    def test_create_forbidden_value_2(self) -> None:
        response = self.request(
            "motion_state.create",
            {
                "name": "test_Xcdfgee",
                "workflow_id": 1,
                "restrictions": ["is__XXXX__submitter"],
            },
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "Action motion_state.create: data.restrictions[0] must be one of ['motion.can_see_internal', 'motion.can_manage_metadata', 'motion.can_manage', 'is_submitter']",
            response.json["message"],
        )

    def test_create_no_permissions(self) -> None:
        self.base_permission_test(
            {}, "motion_state.create", {"name": "test_Xcdfgee", "workflow_id": 1}
        )

    def test_create_permissions(self) -> None:
        self.base_permission_test(
            {},
            "motion_state.create",
            {"name": "test_Xcdfgee", "workflow_id": 1},
            Permissions.Motion.CAN_MANAGE,
        )

    def test_create_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {}, "motion_state.create", {"name": "test_Xcdfgee", "workflow_id": 1}
        )
