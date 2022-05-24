from typing import Any, Dict

from ....models.models import Poll
from ....shared.exceptions import ActionException
from ....shared.patterns import to_fqid
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .mixins import PollPermissionMixin, StopControl


@register_action("poll.publish")
class PollPublishAction(StopControl, UpdateAction, PollPermissionMixin):
    """
    Action to publish a poll.
    """

    model = Poll()
    schema = DefaultSchema(Poll()).get_update_schema()

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        poll = self.datastore.get(
            to_fqid(self.model.collection, instance["id"]), ["state"]
        )
        if poll.get("state") not in [Poll.STATE_FINISHED, Poll.STATE_STARTED]:
            raise ActionException(
                f"Cannot publish poll {instance['id']}, because it is not in state finished or started."
            )
        if poll["state"] == Poll.STATE_STARTED:
            self.on_stop(instance)

        instance["state"] = Poll.STATE_PUBLISHED
        return instance
