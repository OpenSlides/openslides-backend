from collections.abc import Callable
from typing import Any

from openslides_backend.action.mixins.extend_history_mixin import ExtendHistoryMixin

from ....models.models import Poll
from ....services.database.commands import GetManyRequest
from ....shared.exceptions import ActionException, VoteServiceException
from ....shared.patterns import fqid_from_collection_and_id
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from .mixins import PollHistoryMixin, PollPermissionMixin, StopControl


@register_action("poll.stop")
class PollStopAction(
    ExtendHistoryMixin,
    StopControl,
    UpdateAction,
    PollPermissionMixin,
    PollHistoryMixin,
):
    """
    Action to stop a poll.
    """

    model = Poll()
    schema = DefaultSchema(Poll()).get_update_schema()
    poll_history_information = "stopped"
    extend_history_to = "content_object_id"

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
                ["meeting_user_ids"],
            ),
        ]
        result = self.datastore.get_many(requests,
            use_changed_models=False,
            lock_result=False,
        )
        groups = result["group"].values()
        result = self.datastore.get_many(
            [
                GetManyRequest(
                    "meeting_user",
                    list(
                        {
                            meeting_user_id
                            for group in groups
                            for meeting_user_id in group.get("meeting_user_ids", [])
                        }
                    ),
                    ["user_id"],
                ),
            ],
            use_changed_models=False,
            lock_result=False,
        )
        meeting_users = result["meeting_user"].values()
        self.datastore.get_many(
            [
                GetManyRequest(
                    "user",
                    list({mu["user_id"] for mu in meeting_users}),
                    [
                        "poll_voted_ids",
                        "delegated_vote_ids",
                        "vote_ids",
                    ],
                ),
            ],
            use_changed_models=False,
            lock_result=False,
        )

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        poll = self.datastore.get(
            fqid_from_collection_and_id(self.model.collection, instance["id"]),
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
