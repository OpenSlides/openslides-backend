from typing import Set

from openslides_backend.action.util.typing import ActionData
from openslides_backend.services.datastore.commands import GetManyRequest

from ....models.models import Vote
from ...mixins.create_action_with_inferred_meeting import (
    CreateActionWithInferredMeeting,
)
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("vote.create", action_type=ActionType.BACKEND_INTERNAL)
class VoteCreate(CreateActionWithInferredMeeting):
    """
    Internal action to create a vote.
    """

    model = Vote()
    schema = DefaultSchema(Vote()).get_create_schema(
        required_properties=[
            "weight",
            "value",
            "option_id",
            "user_token",
        ],
        optional_properties=["delegated_user_id", "user_id"],
    )

    relation_field_for_meeting = "option_id"

    def prefetch(self, action_data: ActionData) -> None:
        result = self.datastore.get_many(
            [
                GetManyRequest(
                    "option",
                    list({instance["option_id"] for instance in action_data}),
                    ["meeting_id", "vote_ids"],
                ),
            ],
            use_changed_models=False,
        )
        fields = [
            "vote_ids",
            "poll_voted_ids",
            "vote_delegated_vote_$_ids",
        ]
        fields_set: Set[str] = set()
        for option in result["option"].values():
            fields_set.update(
                (
                    f"poll_voted_${option['meeting_id']}_ids",
                    f"vote_delegated_vote_${option['meeting_id']}_ids",
                )
            )
        fields.extend(fields_set)
        self.datastore.get_many(
            [
                GetManyRequest(
                    "user",
                    list(
                        {
                            user_id
                            for instance in action_data
                            for user_id in (
                                instance.get("user_id"),
                                instance.get("delegated_user_id"),
                            )
                            if user_id is not None
                        }
                    ),
                    fields,
                ),
            ],
            use_changed_models=False,
        )
