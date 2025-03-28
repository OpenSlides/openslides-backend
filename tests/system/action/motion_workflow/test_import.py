from typing import Any

from tests.system.action.base import BaseActionTestCase


class MotionWorkflowImport(BaseActionTestCase):
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
        }

    def test_import_simple_case(self) -> None:
        self.create_model(
            "meeting/42",
            {
                "name": "test_name_fsdksjdfhdsfssdf",
                "is_active_in_organization_id": 1,
                "committee_id": 1,
            },
        )
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
            "motion_workflow/1",
            {
                "name": "test_Xcdfgee",
                "first_state_id": 1,
                "sequential_number": 1,
            },
        )
        self.assert_model_exists(
            "motion_state/1",
            {
                "workflow_id": 1,
                "name": "begin",
                "first_state_of_workflow_id": 1,
                "weight": 1,
                "set_workflow_timestamp": True,
                "allow_motion_forwarding": True,
            },
        )

    def test_import_one_state_no_first_state_name(self) -> None:
        self.create_model(
            "meeting/42",
            {
                "name": "test_name_fsdksjdfhdsfssdf",
                "is_active_in_organization_id": 1,
                "committee_id": 1,
            },
        )
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
            "motion_workflow/1",
            {
                "name": "test_Xcdfgee",
                "first_state_id": 1,
            },
        )
        self.assert_model_exists(
            "motion_state/1",
            {"workflow_id": 1, "name": "begin", "first_state_of_workflow_id": 1},
        )

    def test_import_missing_state(self) -> None:
        self.create_model(
            "meeting/42",
            {
                "name": "test_name_fsdksjdfhdsfssdf",
                "is_active_in_organization_id": 1,
                "committee_id": 1,
            },
        )
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
        assert (
            "Some state names in first_state_name or next_state_names or previous_state_names are not found in the state list."
            in response.json["message"]
        )

    def test_import_missing_state_next(self) -> None:
        self.create_model(
            "meeting/42",
            {
                "name": "test_name_fsdksjdfhdsfssdf",
                "is_active_in_organization_id": 1,
                "committee_id": 1,
            },
        )
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
        assert (
            "Some state names in first_state_name or next_state_names or previous_state_names are not found in the state list."
            in response.json["message"]
        )

    def test_import_missing_state_previous(self) -> None:
        self.create_model(
            "meeting/42",
            {
                "name": "test_name_fsdksjdfhdsfssdf",
                "is_active_in_organization_id": 1,
                "committee_id": 1,
            },
        )
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
        assert (
            "Some state names in first_state_name or next_state_names or previous_state_names are not found in the state list."
            in response.json["message"]
        )

    def test_import_next_previous_states(self) -> None:
        self.create_model(
            "meeting/42",
            {
                "name": "test_name_fsdksjdfhdsfssdf",
                "is_active_in_organization_id": 1,
                "committee_id": 1,
            },
        )
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
            "motion_workflow/1",
            {
                "name": "test_Xcdfgee",
                "first_state_id": 1,
            },
        )
        self.assert_model_exists(
            "motion_state/1",
            {
                "workflow_id": 1,
                "name": "begin",
                "first_state_of_workflow_id": 1,
                "next_state_ids": [2, 3],
                "weight": 10,
            },
        )
        self.assert_model_exists(
            "motion_state/2",
            {
                "workflow_id": 1,
                "name": "edit",
                "next_state_ids": [4],
                "previous_state_ids": [1],
                "weight": 11,
            },
        )
        self.assert_model_exists(
            "motion_state/3",
            {
                "workflow_id": 1,
                "name": "read",
                "next_state_ids": [],
                "previous_state_ids": [1],
                "weight": 12,
            },
        )
        self.assert_model_exists(
            "motion_state/4",
            {
                "workflow_id": 1,
                "name": "end",
                "next_state_ids": [],
                "previous_state_ids": [2],
                "weight": 13,
            },
        )

    def test_import_wrong_prev_state(self) -> None:
        self.create_model(
            "meeting/42",
            {
                "name": "test_name_fsdksjdfhdsfssdf",
                "is_active_in_organization_id": 1,
                "committee_id": 1,
            },
        )
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
        assert "State begin is not in previous of edit." in response.json["message"]

    def test_import_wrong_next_state(self) -> None:
        self.create_model(
            "meeting/42",
            {
                "name": "test_name_fsdksjdfhdsfssdf",
                "is_active_in_organization_id": 1,
                "committee_id": 1,
            },
        )
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
        assert "State edit is not in next of begin." in response.json["message"]
