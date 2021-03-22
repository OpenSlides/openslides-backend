import time
from typing import Any, Dict

from ....models.models import Poll
from ....shared.exceptions import ActionException
from ....shared.patterns import Collection, FullQualifiedId
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ..projector_countdown.update import ProjectorCountdownUpdate


@register_action("poll.start")
class PollStartAction(UpdateAction):
    """
    Action to start a poll.
    """

    model = Poll()
    schema = DefaultSchema(Poll()).get_update_schema()

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        poll = self.datastore.get(
            FullQualifiedId(self.model.collection, instance["id"]),
            ["state", "meeting_id"],
        )
        if poll.get("state") != Poll.STATE_CREATED:
            raise ActionException(
                f"Cannot start poll {instance['id']}, because it is not in state created."
            )
        instance["state"] = Poll.STATE_STARTED

        # restart projector countdown given by the meeting
        meeting = self.datastore.get(
            FullQualifiedId(Collection("meeting"), poll["meeting_id"]),
            [
                "poll_couple_countdown",
                "poll_countdown_id",
            ],
        )
        if meeting.get("poll_couple_countdown") and meeting.get("poll_countdown_id"):
            countdown = self.datastore.get(
                FullQualifiedId(
                    Collection("projector_countdown"),
                    meeting["poll_countdown_id"],
                ),
                ["default_time"],
            )
            now = round(time.time())
            self.execute_other_action(
                ProjectorCountdownUpdate,
                [
                    {
                        "id": meeting["poll_countdown_id"],
                        "running": True,
                        "countdown_time": countdown["default_time"] + now,
                    }
                ],
            )
        return instance
