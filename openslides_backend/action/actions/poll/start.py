from typing import Any, Dict

from ....models.models import Poll
from ....shared.exceptions import ActionException
from ....shared.patterns import FullQualifiedId
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("poll.start")
class PollStartAction(UpdateAction):
    """
    Action to start a poll.
    """

    model = Poll()
    schema = DefaultSchema(Poll()).get_update_schema()

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        poll = self.datastore.get(
            FullQualifiedId(self.model.collection, instance["id"]), ["state"]
        )
        if poll.get("state") != Poll.STATE_CREATED:
            raise ActionException(
                f"Cannot start poll {instance['id']}, because it is not in state created."
            )
        instance["state"] = Poll.STATE_STARTED
        return instance
