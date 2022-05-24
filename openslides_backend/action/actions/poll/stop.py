from typing import Any, Callable, Dict

from ....models.models import Poll
from ....services.datastore.commands import GetManyRequest
from ....shared.exceptions import ActionException, VoteServiceException
from ....shared.patterns import to_fqid
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from .mixins import PollPermissionMixin, StopControl


@register_action("poll.stop")
class PollStopAction(StopControl, UpdateAction, PollPermissionMixin):
    """
    Action to stop a poll.
    """

    model = Poll()
    schema = DefaultSchema(Poll()).get_update_schema()

    def prefetch(self, action_data: ActionData) -> None:
        result = self.datastore.get_many(
            [
                GetManyRequest(
                    "poll",
                    list({instance["id"] for instance in action_data}),
                    [
                        "content_object_id",
                        "meeting_id",
                        "state",
                        "voted_ids",
                        "pollmethod",
                        "global_option_id",
                        "entitled_group_ids",
                    ],
                ),
            ],
            use_changed_models=False,
        )
        polls = result["poll"].values()
        meeting_ids = list({poll["meeting_id"] for poll in polls})
        requests = [
            GetManyRequest(
                "meeting",
                meeting_ids,
                [
                    "is_active_in_organization_id",
                    "name",
                    "poll_couple_countdown",
                    "poll_countdown_id",
                    "users_enable_vote_weight",
                    "vote_ids",
                ],
            ),
            GetManyRequest(
                "group",
                list(
                    {
                        group_id
                        for poll in polls
                        for group_id in poll.get("entitled_group_ids", [])
                    }
                ),
                ["user_ids"],
            ),
        ]
        self.datastore.get_many(requests, use_changed_models=False)

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        poll = self.datastore.get(
            to_fqid(self.model.collection, instance["id"]),
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
                try:
                    self.vote_service.clear(instance["id"])
                except VoteServiceException as e:
                    self.logger.error(f"Error clearing vote {instance['id']}: {str(e)}")

        return on_success
