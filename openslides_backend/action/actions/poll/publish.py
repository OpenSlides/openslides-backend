from typing import Any

from openslides_backend.action.mixins.extend_history_mixin import ExtendHistoryMixin
from openslides_backend.shared.typing import HistoryInformation

from ....models.models import Poll
from ....shared.exceptions import ActionException
from ....shared.patterns import fqid_from_collection_and_id
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .mixins import PollHistoryMixin, PollPermissionMixin, StopControl


@register_action("poll.publish")
class PollPublishAction(
    ExtendHistoryMixin,
    StopControl,
    UpdateAction,
    PollPermissionMixin,
    PollHistoryMixin,
):
    """
    Action to publish a poll.
    """

    model = Poll()
    schema = DefaultSchema(Poll()).get_update_schema()
    extend_history_to = "content_object_id"

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        poll = self.datastore.get(
            fqid_from_collection_and_id(self.model.collection, instance["id"]),
            ["state"],
        )
        if poll.get("state") not in [Poll.STATE_FINISHED, Poll.STATE_STARTED]:
            raise ActionException(
                f"Cannot publish poll {instance['id']}, because it is not in state finished or started."
            )
        if poll["state"] == Poll.STATE_STARTED:
            self.on_stop(instance)

        instance["state"] = Poll.STATE_PUBLISHED
        return instance

    def get_history_information(self) -> HistoryInformation | None:
        polls = self.get_instances_with_fields(["content_object_id", "state"])
        return {
            poll["content_object_id"]: [
                f"{self.get_history_title(poll)} {'stopped/' if poll['state'] != Poll.STATE_FINISHED else ''}published"
            ]
            for poll in polls
        }
