from typing import cast

from openslides_backend.action.util.typing import ActionData
from openslides_backend.services.database.commands import GetManyRequest

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
        self.datastore.get_many(
            [
                GetManyRequest(
                    "option",
                    list({instance["option_id"] for instance in action_data}),
                    ["meeting_id", "vote_ids"],
                ),
            ],
            use_changed_models=False,
        )
        meeting_users = self.datastore.get_many(
            [
                GetManyRequest(
                    "meeting_user",
                    list(
                        {
                            cast(int, instance.get(fname))
                            for instance in action_data
                            for fname in (
                                "meeting_user_id",
                                "delegated_meeting_user_id",
                            )
                            if instance.get(fname)
                        }
                    ),
                    ["id", "user_id", "vote_ids", "delegated_vote_ids"],
                ),
            ],
            use_changed_models=False,
            lock_result=False,
        )["meeting_user"]

        self.datastore.get_many(
            [
                GetManyRequest(
                    "user",
                    list({mu["user_id"] for mu in meeting_users.values()}),
                    ["id", "poll_voted_ids"],
                ),
            ],
            use_changed_models=False,
            lock_result=False,
        )
