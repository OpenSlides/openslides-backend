from typing import Any, Callable, Dict, Tuple, Optional

from ....models.models import Poll
from ....shared.exceptions import ActionException
from ....shared.patterns import FullQualifiedId, Collection
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from .mixins import PollPermissionMixin, StopControl

from ....services.datastore.commands import GetManyRequest
from ....shared.interfaces.write_request import WriteRequest
from ...util.typing import ActionResults


@register_action("poll.stop")
class PollStopAction(StopControl, UpdateAction, PollPermissionMixin):
    """
    Action to stop a poll.
    """

    model = Poll()
    schema = DefaultSchema(Poll()).get_update_schema()

    def perform(
        self, action_data: ActionData, user_id: int, internal: bool = False
    ) -> Tuple[Optional[WriteRequest], Optional[ActionResults]]:
        self.prefetch(action_data, user_id)
        return super().perform(action_data, user_id, internal)
    
    def prefetch(self, action_data: ActionData, user_id: int) -> None:
        result = self.datastore.get_many([
            GetManyRequest(Collection("meeting"), [1], ["is_active_in_organization_id", "name", 'poll_couple_countdown', 'poll_countdown_id', 'users_enable_vote_weight', "vote_ids"]),
            GetManyRequest(Collection("group"), [3], ["user_ids"]),
            GetManyRequest(Collection("poll"), [1], ["content_object_id", "meeting_id", "state", "voted_ids", 'pollmethod', 'global_option_id', 'entitled_group_ids']),
            GetManyRequest(Collection("option"), [1], ["meeting_id", "vote_ids"]),
            GetManyRequest(Collection("user"), list(range(1, 102)), ['group_$1_ids', 'organization_management_level', "vote_$_ids", 'vote_$1_ids', 'vote_delegated_vote_$_ids', 'vote_delegated_vote_$1_ids', 'poll_voted_$_ids', 'poll_voted_$1_ids', "is_present_in_meeting_ids", "vote_delegated_$_to_id", "vote_delegated_$1_to_id"])
        ])

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
        self.on_stop(instance)
        return instance

    def get_on_success(self, action_data: ActionData) -> Callable[[], None]:
        def on_success() -> None:
            for instance in action_data:
                self.vote_service.clear(instance["id"])

        return on_success
