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
            "is_present_in_meeting_ids",
            "organization_management_level",
            "group_$_ids",
            "vote_$_ids",
            "poll_voted_$_ids",
            "vote_delegated_$_to_id",
            "vote_delegated_vote_$_ids",
        ]
        for option in result["option"].values():
            fields.extend(
                (
                    f"group_${option['meeting_id']}_ids",
                    f"vote_${option['meeting_id']}_ids",
                    f"poll_voted_${option['meeting_id']}_ids",
                    f"vote_delegated_${option['meeting_id']}_to_id",
                    f"vote_delegated_vote_${option['meeting_id']}_ids",
                )
            )
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
