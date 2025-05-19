from collections.abc import Callable

from ....models.models import Poll
from ....services.datastore.interface import GetManyRequest
from ....shared.exceptions import VoteServiceException
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from .mixins import PollHistoryMixin, PollPermissionMixin


@register_action("poll.delete")
class PollDelete(DeleteAction, PollPermissionMixin, PollHistoryMixin):
    """
    Action to delete polls.
    """

    model = Poll()
    schema = DefaultSchema(Poll()).get_delete_schema()
    poll_history_information = "deleted"

    def prefetch(self, action_data: ActionData) -> None:
        result = self.datastore.get_many(
            [
                GetManyRequest(
                    "poll",
                    list({instance["id"] for instance in action_data}),
                    [
                        "content_object_id",
                        "meeting_id",
                        "entitled_group_ids",
                        "voted_ids",
                        "option_ids",
                        "global_option_id",
                        "projection_ids",
                        "meta_deleted",
                        "meta_position",
                        "state",
                    ],
                ),
            ],
            use_changed_models=False,
        )
        polls = result["poll"].values()
        self.started_polls = [
            id_
            for id_, poll in result["poll"].items()
            if poll.get("state") == "started"
        ]
        meeting_ids = list({poll["meeting_id"] for poll in polls})
        group_ids = list(
            {
                group_id
                for poll in polls
                for group_id in poll.get("entitled_group_ids", ())
            }
        )
        option_ids = [
            option_id
            for poll in polls
            if poll.get("option_ids")
            for option_id in poll["option_ids"]
        ]
        requests = [
            GetManyRequest(
                "meeting",
                meeting_ids,
                [
                    "is_active_in_organization_id",
                    "name",
                    "option_ids",
                    "poll_ids",
                ],
            ),
            GetManyRequest(
                "option",
                option_ids,
                [
                    "meeting_id",
                    "vote_ids",
                    "content_object_id",
                    "poll_id",
                    "used_as_global_option_in_poll_id",
                    "vote_ids",
                    "meta_deleted",
                    "meta_position",
                ],
            ),
            GetManyRequest(
                "group",
                group_ids,
                ["poll_ids"],
            ),
        ]
        self.datastore.get_many(requests, use_changed_models=False)

    def get_on_success(self, action_data: ActionData) -> Callable[[], None]:
        def on_success() -> None:
            for instance in action_data:
                if (id_ := instance["id"]) in self.started_polls:
                    try:
                        self.vote_service.clear(id_)
                    except VoteServiceException as e:
                        self.logger.error(f"Error clearing vote {id_}: {str(e)}")

        return on_success
