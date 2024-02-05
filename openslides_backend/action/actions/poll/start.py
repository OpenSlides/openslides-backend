from collections.abc import Callable
from typing import Any

from openslides_backend.action.mixins.extend_history_mixin import ExtendHistoryMixin

from ....models.models import Poll
from ....shared.exceptions import ActionException, VoteServiceException
from ....shared.patterns import fqid_from_collection_and_id
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from ..projector_countdown.mixins import CountdownControl
from .mixins import PollHistoryMixin, PollPermissionMixin


@register_action("poll.start")
class PollStartAction(
    ExtendHistoryMixin,
    CountdownControl,
    UpdateAction,
    PollPermissionMixin,
    PollHistoryMixin,
):
    """
    Action to start a poll.
    """

    model = Poll()
    schema = DefaultSchema(Poll()).get_update_schema()
    poll_history_information = "started"
    extend_history_to = "content_object_id"

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        poll = self.datastore.get(
            fqid_from_collection_and_id(self.model.collection, instance["id"]),
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
            fqid_from_collection_and_id("meeting", poll["meeting_id"]),
            [
                "poll_couple_countdown",
                "poll_countdown_id",
            ],
        )
        if meeting.get("poll_couple_countdown") and meeting.get("poll_countdown_id"):
            self.control_countdown(meeting["poll_countdown_id"], "restart")

        self.vote_service.start(instance["id"])

        return instance

    def get_on_failure(self, action_data: ActionData) -> Callable[[], None]:
        def on_failure() -> None:
            for instance in action_data:
                try:
                    self.vote_service.clear(instance["id"])
                except VoteServiceException as e:
                    self.logger.error(f"Error clearing vote {instance['id']}: {str(e)}")

        return on_failure
