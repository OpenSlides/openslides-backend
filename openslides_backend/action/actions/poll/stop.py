from decimal import Decimal
from typing import Any, Dict, List

from ....models.models import Poll
from ....services.datastore.commands import GetManyRequest
from ....shared.exceptions import ActionException
from ....shared.patterns import Collection, FullQualifiedId
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ..projector_countdown.mixins import CountdownControl
from .mixins import PollPermissionMixin


@register_action("poll.stop")
class PollStopAction(CountdownControl, UpdateAction, PollPermissionMixin):
    """
    Action to stop a poll.
    """

    model = Poll()
    schema = DefaultSchema(Poll()).get_update_schema()

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        poll = self.datastore.get(
            FullQualifiedId(self.model.collection, instance["id"]),
            ["state", "meeting_id", "voted_ids"],
        )
        if poll.get("state") != Poll.STATE_STARTED:
            raise ActionException(
                f"Cannot stop poll {instance['id']}, because it is not in state started."
            )
        instance["state"] = Poll.STATE_FINISHED

        # reset countdown given by meeting
        meeting = self.datastore.get(
            FullQualifiedId(Collection("meeting"), poll["meeting_id"]),
            [
                "poll_couple_countdown",
                "poll_countdown_id",
                "users_enable_vote_weight",
            ],
        )
        if meeting.get("poll_couple_countdown") and meeting.get("poll_countdown_id"):
            self.control_countdown(meeting["poll_countdown_id"], "reset")

        # calculate votescast, votesvalid, votesinvalid
        voted_ids = poll.get("voted_ids", [])
        instance["votescast"] = str(Decimal("0.000000") + Decimal(len(voted_ids)))
        if not meeting.get("users_enable_vote_weight") or not voted_ids:
            instance["votesvalid"] = instance["votescast"]
        else:
            gmr = GetManyRequest(
                Collection("user"), voted_ids, [f"vote_weight_${poll['meeting_id']}"]
            )
            gm_result = self.datastore.get_many([gmr])
            users = gm_result.get(Collection("user"), {}).values()
            instance["votesvalid"] = str(
                sum(
                    Decimal(entry.get(f"vote_weight_${poll['meeting_id']}", "1.000000"))
                    for entry in users
                )
            )
        instance["votesinvalid"] = "0.000000"

        # set entitled users at stop.
        instance["entitled_users_at_stop"] = self.get_entitled_user(poll)
        return instance

    def get_entitled_user(self, poll: Dict[str, Any]) -> List[Dict[str, Any]]:
        entitled_users = []
        entitled_users_ids = set()
        all_voted_users = poll.get("voted_ids", [])
        meeting_id = poll["meeting_id"]

        # get all users from the groups.
        meeting = self.datastore.get(
            FullQualifiedId(Collection("meeting"), meeting_id), ["group_ids"]
        )
        gmr = GetManyRequest(
            Collection("group"), meeting.get("group_ids", []), ["user_ids"]
        )
        gm_result = self.datastore.get_many([gmr])
        groups = gm_result.get(Collection("group"), {}).values()

        for group in groups:
            user_ids = group.get("user_ids", [])
            if not user_ids:
                continue
            gmr = GetManyRequest(
                Collection("user"),
                list(user_ids),
                [
                    "id",
                    "is_present_in_meeting_ids",
                    f"vote_delegated_${meeting_id}_to_id",
                ],
            )
            gm_result = self.datastore.get_many([gmr])
            users = gm_result.get(Collection("user"), {}).values()
            for user in users:
                vote_delegated = {}
                if user.get(f"vote_delegated_${meeting_id}_to_id"):
                    vote_delegated = self.datastore.get(
                        FullQualifiedId(
                            Collection("user"),
                            user[f"vote_delegated_${meeting_id}_to_id"],
                        ),
                        ["is_present_in_meeting_ids"],
                    )

                if user["id"] in entitled_users_ids:
                    continue
                elif poll["meeting_id"] in user.get(
                    "is_present_in_meeting_ids", []
                ) or (
                    user.get(f"vote_delegated_${meeting_id}_to_id")
                    and poll["meeting_id"]
                    in vote_delegated.get("is_present_in_meeting_ids", [])
                ):
                    entitled_users_ids.add(user["id"])
                    entitled_users.append(
                        {
                            "user_id": user["id"],
                            "voted": user["id"] in all_voted_users,
                            "vote_delegated_to_id": user.get(
                                f"vote_delegated_${meeting_id}_to_id"
                            ),
                        }
                    )

        return entitled_users
