from ....models.models import Poll
from ....services.datastore.interface import GetManyRequest
from ....shared.patterns import Collection
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from .mixins import PollPermissionMixin


@register_action("poll.delete")
class PollDelete(DeleteAction, PollPermissionMixin):
    """
    Action to delete polls.
    """

    model = Poll()
    schema = DefaultSchema(Poll()).get_delete_schema()

    def prefetch(self, action_data: ActionData) -> None:
        result = self.datastore.get_many(
            [
                GetManyRequest(
                    Collection("poll"),
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
                    ],
                ),
            ],
            use_changed_models=False,
        )
        polls = result[Collection("poll")].values()
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
                Collection("meeting"),
                meeting_ids,
                [
                    "is_active_in_organization_id",
                    "name",
                    "option_ids",
                    "poll_ids",
                ],
            ),
            GetManyRequest(
                Collection("option"),
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
                Collection("group"),
                group_ids,
                ["poll_ids"],
            ),
        ]
        self.datastore.get_many(requests, use_changed_models=False)
