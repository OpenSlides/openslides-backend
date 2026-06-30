from typing import Any
from ....shared.typing import Schema

from ...action import Action
from .create import MeetingPollDefaultCreate
from ....shared.filters import Filter, FilterOperator
from ....models.models import MeetingPollDefault

# from ...shared.filters import And, Filter, FilterOperator

settings_fields_types: Schema = {
    "allow_abstain": {"type": "boolean"},
    "allow_nota": {"type": "boolean"},
    "ballot_paper_selection": {"type": "string"},
    "ballot_paper_number": {"type": "integer"},
    "group_ids": {
        "type": "array",
        "items": {"type": "integer"},
        "uniqueItems": True,
    },
    "display_chart": {"type": "string"},
    "onehundred_percent_base": {"type": "string"},
    "sort_result_by_votes": {"type": "boolean"},
    "strike_out": {"type": "boolean"},
    "visibility": {"type": "string"},
}

# TODO: into meeting helper. Or most of this file as meeting mixin
meeting_poll_default_schema = {
    f"{poll_type}_poll_default_{field_name}": type_
    for poll_type in MeetingPollDefault.POLL_TYPES
    for field_name, type_ in settings_fields_types.items()
}


class MeetingPollDefaultHelperMixin(Action):
    def get_meeting_poll_default_field_name(poll_type: str) -> Filter:
        return f"{poll_type}_poll_default_method"

    def get_meeting_poll_default_back_relation(poll_type: str) -> Filter:
        return f"used_as_{poll_type}_poll_config_in_meeting_id"

    def get_meeting_poll_default_filter(
        self, meeting_id: int, poll_type_field_name: str
    ) -> Filter:
        return FilterOperator(poll_type_field_name, "=", meeting_id)

    def get_meeting_poll_default(
        self, meeting_id: int, poll_type_field_name: str, fields: list[str] = ["id"]
    ) -> dict[str, Any] | None:
        result = self.datastore.filter(
            "meeting_poll_default",
            self.get_meeting_poll_default_filter(meeting_id, poll_type_field_name),
            fields,
            lock_result=False,
        )
        if result:
            return next(iter(result.values()))
        return None

    def create_meeting_poll_default(
        self,
        meeting_id: int,
        poll_type: str,
        model_data: dict[str, Any],
    ) -> int:
        action_results = self.execute_other_action(
            MeetingPollDefaultCreate,
            [
                {
                    "meeting_id": meeting_id,
                    self.get_meeting_poll_default_back_relation(poll_type): meeting_id,
                    **model_data,
                }
            ],
        )
        return action_results[0]["id"]
