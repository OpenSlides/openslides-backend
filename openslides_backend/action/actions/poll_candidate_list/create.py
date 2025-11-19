from typing import Any

from ....models.models import PollCandidateList
from ....shared.schema import required_id_schema
from ...generics.create import CreateAction
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ..poll_candidate.create import PollCandidateCreate

entry_schema = {
    "description": "An entry in a poll_candidate_list create schema",
    "type": "object",
    "properties": {
        "user_id": required_id_schema,
        "weight": {"type": "integer"},
    },
    "additionalProperties": False,
}


@register_action("poll_candidate_list.create", action_type=ActionType.BACKEND_INTERNAL)
class PollCandidateListCreate(CreateAction):
    """
    Internal action to create a poll_candidate_list.
    """

    model = PollCandidateList()
    schema = DefaultSchema(PollCandidateList()).get_create_schema(
        required_properties=["option_id", "meeting_id"],
        additional_required_fields={
            "entries": {"type": "array", "items": entry_schema, "minItems": 1}
        },
    )

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        instance = super().update_instance(instance)
        entries = instance.pop("entries")
        self.apply_instance(instance)
        res = self.execute_other_action(
            PollCandidateCreate,
            [
                {
                    "user_id": entry["user_id"],
                    "weight": entry["weight"],
                    "poll_candidate_list_id": instance["id"],
                    "meeting_id": instance["meeting_id"],
                }
                for entry in entries
            ],
        )
        instance["poll_candidate_ids"] = [r["id"] for r in res]  # type: ignore
        return instance
