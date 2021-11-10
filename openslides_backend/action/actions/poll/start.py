from typing import Any, Callable, Dict

from ....models.models import Poll
from ....shared.exceptions import ActionException
from ....shared.patterns import Collection, FullQualifiedId
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from ..projector_countdown.mixins import CountdownControl
from .mixins import PollPermissionMixin


@register_action("poll.start")
class PollStartAction(CountdownControl, UpdateAction, PollPermissionMixin):
    """
    Action to start a poll.
    """

    model = Poll()
    schema = DefaultSchema(Poll()).get_update_schema()

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        poll = self.datastore.get(
            FullQualifiedId(self.model.collection, instance["id"]),
            ["state", "meeting_id", "type"],
        )
        if poll.get("type") == Poll.TYPE_ANALOG:
            raise ActionException(
                "Analog polls cannot be started. Please use poll.update instead to give votes."
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
            self.control_countdown(meeting["poll_countdown_id"], "restart")
        return instance

    def get_on_success(self, action_data: ActionData) -> Callable[[], None]:
        def on_success() -> None:
            for instance in action_data:
                self.vote_service.start(instance["id"])

        return on_success
