import copy
from typing import Any

from ....models.models import MotionState, MotionWorkflow
from ....permissions.permissions import Permissions
from ....shared.exceptions import ActionException
from ....shared.schema import str_list_schema
from ...mixins.sequential_numbers_mixin import SequentialNumbersMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ..motion_state.create import MotionStateCreateAction
from ..motion_state.update import MotionStateUpdateAction


@register_action("motion_workflow.import")
class MotionWorkflowImport(SequentialNumbersMixin):
    """
    Action to import a motion workflow.
    """

    model = MotionWorkflow()
    schema = DefaultSchema(MotionWorkflow()).get_default_schema(
        required_properties=["name", "meeting_id"],
        additional_optional_fields={
            "first_state_name": {"type": "string"},
            "states": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        **MotionState().get_properties(
                            "name",
                            "weight",
                            "recommendation_label",
                            "css_class",
                            "restrictions",
                            "allow_support",
                            "allow_create_poll",
                            "allow_submitter_edit",
                            "set_number",
                            "show_state_extension_field",
                            "show_recommendation_extension_field",
                            "merge_amendment_into_final",
                            "set_workflow_timestamp",
                            "allow_motion_forwarding",
                        ),
                        "next_state_names": str_list_schema,
                        "previous_state_names": str_list_schema,
                    },
                    "additionalProperties": False,
                },
            },
        },
    )
    permission = Permissions.Motion.CAN_MANAGE

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        instance = super().update_instance(instance)
        first_state_name = instance.pop("first_state_name", "")
        states = instance.pop("states", [])
        self.apply_instance(instance)
        self.check_states(first_state_name, states)

        # create the states.
        action_data = []
        first = True
        for state in states:
            state_data = copy.deepcopy(state)
            if first_state_name and first_state_name == state_data["name"]:
                state_data["first_state_of_workflow_id"] = instance["id"]
            elif not first_state_name and first:
                state_data["first_state_of_workflow_id"] = instance["id"]
            del state_data["next_state_names"]
            del state_data["previous_state_names"]
            state_data["workflow_id"] = instance["id"]
            action_data.append(state_data)
            first = False
        action_results = self.execute_other_action(
            MotionStateCreateAction,
            action_data,
        )

        # calculate name to id map.
        self.name_to_id: dict[str, int] = {}
        for idx, state in enumerate(states):
            name = state.get("name")
            if name in self.name_to_id:
                raise ActionException(f"State name {name} not unique.")
            self.name_to_id[name] = action_results[idx]["id"]  # type: ignore

        # add first_state_id, next_state_ids and previous_state_ids
        action_data = []
        for state in states:
            data: dict[str, Any] = {"id": self.name_to_id[state["name"]]}
            data["next_state_ids"] = [
                self.name_to_id[state_tmp] for state_tmp in state["next_state_names"]
            ]
            data["previous_state_ids"] = [
                self.name_to_id[state_tmp]
                for state_tmp in state["previous_state_names"]
            ]
            action_data.append(data)
        self.execute_other_action(
            MotionStateUpdateAction,
            action_data,
        )

        return instance

    def check_states(self, first_state_name: str, states: list[dict[str, Any]]) -> None:
        found_names = {state["name"] for state in states}
        needed_names = set()
        if first_state_name:
            needed_names.add(first_state_name)
        for state in states:
            for name in state["next_state_names"]:
                needed_names.add(name)
            for name in state["previous_state_names"]:
                needed_names.add(name)
        if not needed_names.issubset(found_names):
            raise ActionException(
                "Some state names in first_state_name or next_state_names or previous_state_names are not found in the state list."
            )
        states_dict = {}
        for state in states:
            states_dict[state["name"]] = state
        for state in states:
            for name in state["next_state_names"]:
                if state["name"] not in states_dict[name]["previous_state_names"]:
                    raise ActionException(
                        f"State {state['name']} is not in previous of {name}."
                    )
            for name in state["previous_state_names"]:
                if state["name"] not in states_dict[name]["next_state_names"]:
                    raise ActionException(
                        f"State {state['name']} is not in next of {name}."
                    )
