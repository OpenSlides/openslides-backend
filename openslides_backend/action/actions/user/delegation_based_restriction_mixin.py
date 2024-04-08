from typing import Literal

from openslides_backend.action.action import Action
from openslides_backend.shared.filters import And, FilterOperator, Or

from ....services.datastore.commands import GetManyRequest
from ....shared.exceptions import ActionException

DelegationBasedRestriction = Literal[
    "users_forbid_delegator_in_list_of_speakers",
    "users_forbid_delegator_as_submitter",
    "users_forbid_delegator_as_supporter",
]


class DelegationBasedRestrictionMixin(Action):
    def check_delegator_restriction(
        self,
        restriction: DelegationBasedRestriction,
        meeting_id: int,
        error_message: str,
    ) -> None:
        data = self.datastore.get_many(
            [
                GetManyRequest(
                    "user",
                    [self.user_id],
                    ["is_present_in_meeting_ids", "meeting_user_ids"],
                ),
                GetManyRequest("meeting", [meeting_id], [restriction]),
            ]
        )
        operator = data["user"][self.user_id]
        if (meeting_id in operator.get("is_present_in_meeting_ids", [])) or not data[
            "meeting"
        ][meeting_id].get(restriction):
            return
        if operator.get("meeting_user_ids"):
            meeting_users = self.datastore.filter(
                "meeting_user",
                And(
                    FilterOperator("meeting_id", "=", meeting_id),
                    Or(
                        *[
                            FilterOperator("id", "=", meeting_user_id)
                            for meeting_user_id in operator["meeting_user_ids"]
                        ]
                    ),
                ),
                ["vote_delegated_to_id"],
            )
            if len(meeting_users) and list(meeting_users.values())[0].get(
                "vote_delegated_to_id"
            ):
                raise ActionException(
                    error_message
                    or "Action may not be performed by users who have delegated their vote"
                )
