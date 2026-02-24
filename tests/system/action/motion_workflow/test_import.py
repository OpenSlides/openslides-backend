from typing import Any

from tests.system.action.base import BaseActionTestCase


class MotionWorkflowImport(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting(42)

    def get_state(
        self,
        name: str,
        next_state_names: list[str],
        previous_state_names: list[str],
        weight: int = 1,
    ) -> dict[str, Any]:
        return {
            "name": name,
            "recommendation_label": "",
            "css_class": "grey",
            "restrictions": [],
            "allow_support": True,
            "allow_submitter_edit": False,
            "allow_create_poll": False,
            "set_number": False,
            "show_state_extension_field": False,
            "show_recommendation_extension_field": False,
            "merge_amendment_into_final": None,
            "next_state_names": next_state_names,
            "previous_state_names": previous_state_names,
            "weight": weight,
            "set_workflow_timestamp": True,
            "allow_motion_forwarding": True,
            "allow_amendment_forwarding": True,
        }

    def test_import_simple_case(self) -> None:
        response = self.request(
            "motion_workflow.import",
            {
                "name": "test_Xcdfgee",
                "meeting_id": 42,
                "first_state_name": "begin",
                "states": [
                    self.get_state("begin", [], []),
                ],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion_workflow/43",
            {
                "name": "test_Xcdfgee",
                "first_state_id": 43,
                "sequential_number": 2,
            },
        )
        self.assert_model_exists(
            "motion_state/43",
            {
                "workflow_id": 43,
                "name": "begin",
                "first_state_of_workflow_id": 43,
                "weight": 1,
                "set_workflow_timestamp": True,
                "allow_motion_forwarding": True,
                "allow_amendment_forwarding": True,
            },
        )

    def test_import_one_state_no_first_state_name(self) -> None:
        response = self.request(
            "motion_workflow.import",
            {
                "name": "test_Xcdfgee",
                "meeting_id": 42,
                "first_state_name": "",
                "states": [self.get_state("begin", [], [])],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion_workflow/43",
            {"name": "test_Xcdfgee", "first_state_id": 43},
        )
        self.assert_model_exists(
            "motion_state/43",
            {"workflow_id": 43, "name": "begin", "first_state_of_workflow_id": 43},
        )

    def test_import_missing_state(self) -> None:
        response = self.request(
            "motion_workflow.import",
            {
                "name": "test_Xcdfgee",
                "meeting_id": 42,
                "first_state_name": "test",
                "states": [self.get_state("begin", [], [])],
            },
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "Some state names in first_state_name or next_state_names or previous_state_names are not found in the state list.",
            response.json["message"],
        )

    def test_import_missing_state_next(self) -> None:
        response = self.request(
            "motion_workflow.import",
            {
                "name": "test_Xcdfgee",
                "meeting_id": 42,
                "first_state_name": "",
                "states": [self.get_state("begin", ["test"], [])],
            },
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "Some state names in first_state_name or next_state_names or previous_state_names are not found in the state list.",
            response.json["message"],
        )

    def test_import_missing_state_previous(self) -> None:
        response = self.request(
            "motion_workflow.import",
            {
                "name": "test_Xcdfgee",
                "meeting_id": 42,
                "first_state_name": "begin",
                "states": [self.get_state("begin", [], ["test"])],
            },
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "Some state names in first_state_name or next_state_names or previous_state_names are not found in the state list.",
            response.json["message"],
        )

    def test_import_next_previous_states(self) -> None:
        response = self.request(
            "motion_workflow.import",
            {
                "name": "test_Xcdfgee",
                "meeting_id": 42,
                "first_state_name": "",
                "states": [
                    self.get_state("begin", ["edit", "read"], [], 10),
                    self.get_state("edit", ["end"], ["begin"], 11),
                    self.get_state("read", [], ["begin"], 12),
                    self.get_state("end", [], ["edit"], 13),
                ],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion_workflow/43",
            {
                "name": "test_Xcdfgee",
                "first_state_id": 43,
            },
        )
        self.assert_model_exists(
            "motion_state/43",
            {
                "workflow_id": 43,
                "name": "begin",
                "first_state_of_workflow_id": 43,
                "next_state_ids": [44, 45],
                "weight": 10,
            },
        )
        self.assert_model_exists(
            "motion_state/44",
            {
                "workflow_id": 43,
                "name": "edit",
                "next_state_ids": [46],
                "previous_state_ids": [43],
                "weight": 11,
            },
        )
        self.assert_model_exists(
            "motion_state/45",
            {
                "workflow_id": 43,
                "name": "read",
                "next_state_ids": None,
                "previous_state_ids": [43],
                "weight": 12,
            },
        )
        self.assert_model_exists(
            "motion_state/46",
            {
                "workflow_id": 43,
                "name": "end",
                "next_state_ids": None,
                "previous_state_ids": [44],
                "weight": 13,
            },
        )

    def test_import_wrong_prev_state(self) -> None:
        response = self.request(
            "motion_workflow.import",
            {
                "name": "test_Xcdfgee",
                "meeting_id": 42,
                "first_state_name": "",
                "states": [
                    self.get_state("begin", ["edit", "read"], [], 10),
                    self.get_state("edit", ["end"], [], 11),
                    self.get_state("read", [], ["begin"], 12),
                    self.get_state("end", [], ["edit"], 13),
                ],
            },
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "State begin is not in previous of edit.", response.json["message"]
        )

    def test_import_wrong_next_state(self) -> None:
        response = self.request(
            "motion_workflow.import",
            {
                "name": "test_Xcdfgee",
                "meeting_id": 42,
                "first_state_name": "",
                "states": [
                    self.get_state("begin", ["read"], [], 10),
                    self.get_state("edit", ["end"], ["begin"], 11),
                    self.get_state("read", [], ["begin"], 12),
                    self.get_state("end", [], ["edit"], 13),
                ],
            },
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "State edit is not in next of begin.", response.json["message"]
        )

    def test_import_state_not_unique(self) -> None:
        response = self.request(
            "motion_workflow.import",
            {
                "name": "test_Xcdfgee",
                "meeting_id": 42,
                "first_state_name": "",
                "states": [
                    self.get_state("begin", [], []),
                    self.get_state("begin", [], []),
                    self.get_state("end", [], []),
                ],
            },
        )
        self.assert_status_code(response, 400)
        self.assertEqual("State name begin not unique.", response.json["message"])
