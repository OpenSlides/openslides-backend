from decimal import Decimal
from typing import Any, Dict

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
        instance["votescast"] = f"{len(voted_ids)}.000000"
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
                    [
                        Decimal(
                            entry.get(f"vote_weight_${poll['meeting_id']}", "1.000000")
                        )
                        for entry in users
                    ]
                )
            )
        instance["votesinvalid"] = "0.000000"

        return instance
