from typing import Any, Dict

from ....models.models import Poll
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
            ["state", "meeting_id"],
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
            ],
        )
        if meeting.get("poll_couple_countdown") and meeting.get("poll_countdown_id"):
            self.control_countdown(meeting["poll_countdown_id"], "reset")
        return instance
