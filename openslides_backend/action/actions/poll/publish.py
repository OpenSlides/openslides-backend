from typing import Any, Dict

from openslides_backend.action.mixins.extend_history_mixin import ExtendHistoryMixin

from ....models.models import Poll
from ....shared.exceptions import ActionException
from ....shared.patterns import fqid_from_collection_and_id
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .mixins import PollPermissionMixin, StopControl


@register_action("poll.publish")
class PollPublishAction(
    ExtendHistoryMixin,
    StopControl,
    UpdateAction,
    PollPermissionMixin,
):
    """
    Action to publish a poll.
    """

    model = Poll()
    schema = DefaultSchema(Poll()).get_update_schema()
    history_information = "Voting published"
    extend_history_to = "content_object_id"

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
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
