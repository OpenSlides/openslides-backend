from typing import Any, Callable, Dict

from ....models.models import Poll
from ....services.datastore.commands import GetManyRequest
from ....shared.exceptions import ActionException, VoteServiceException
from ....shared.patterns import fqid_from_collection_and_id
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
        """
        locked fields zu Beginn:
        'poll/1/state', 'poll/1/content_object_id', 'poll/1/voted_ids',
        'poll/1/entitled_group_ids', 'poll/1/global_option_id',
        'poll/1/pollmethod', 'poll/1/meeting_id',
        'meeting/1/is_active_in_organization_id',
        'meeting/1/vote_ids', 'meeting/1/users_enable_vote_weight',
        'meeting/1/name', 'meeting/1/poll_couple_countdown',
        'meeting/1/poll_countdown_id',
        'group/3/user_ids',
        'option/1/meeting_id', 'option/1/vote_ids',
        'user/2/vote_delegated_$_to_id', 'user/2/is_present_in_meeting_ids',
        'user/2/vote_$_ids', 'user/2/vote_delegated_$1_to_id',
        'user/2/vote_delegated_vote_$1_ids',
        'user/2/vote_delegated_vote_$_ids',
        'user/2/group_$1_ids',
        'user/2/organization_management_level',
        'user/2/group_$_ids',
        'user/2/vote_$1_ids',
        'user/2/poll_voted_$1_ids',
        'user/2/poll_voted_$_ids',
        'user/3/vote_delegated_$_to_id', 'user/3/is_present_in_meeting_ids', 'user/3/vote_$_ids', 'user/3/vote_delegated_$1_to_id', 'user/3/vote_delegated_vote_$1_ids', 'user/3/vote_delegated_vote_$_ids', 'user/3/group_$1_ids', 'user/3/organization_management_level', 'user/3/group_$_ids', 'user/3/vote_$1_ids', 'user/3/poll_voted_$1_ids', 'user/3/poll_voted_$_ids',
        'user/4/vote_delegated_$_to_id', 'user/4/is_present_in_meeting_ids', 'user/4/vote_$_ids', 'user/4/vote_delegated_$1_to_id', 'user/4/vote_delegated_vote_$1_ids', 'user/4/vote_delegated_vote_$_ids', 'user/4/group_$1_ids', 'user/4/organization_management_level', 'user/4/group_$_ids', 'user/4/vote_$1_ids', 'user/4/poll_voted_$1_ids', 'user/4/poll_voted_$_ids'

        get:
        'user/1', ['group_$1_ids', 'organization_management_level'])", 1, 28))

        get_many:
        0:{'collection': 'poll', 'ids': [1], 'mapped_fields': ['state', 'content_object_id', 'voted_ids', 'meta_position', 'entitled_group_ids', 'global_option_id', 'pollmethod', 'meeting_id']}
        1:{'collection': 'meeting', 'ids': [1], 'mapped_fields': ['is_active_in_organization_id', 'meta_position', 'vote_ids', 'users_enable_vote_weight', 'name', 'poll_couple_countdown', 'poll_countdown_id']}
        1:{'collection': 'group', 'ids': [3], 'mapped_fields': ['user_ids', 'meta_position']}
        2:{'collection': 'option', 'ids': [1], 'mapped_fields': ['meeting_id', 'vote_ids', 'meta_position']}

        3:{'collection': 'user', 'ids': [2], 'mapped_fields':
            ['vote_delegated_$_to_id', 'is_present_in_meeting_ids',
             'vote_$_ids', 'vote_delegated_$1_to_id',
             'meta_position', 'vote_delegated_vote_$1_ids',
             'vote_delegated_vote_$_ids', 'group_$1_ids',
             'organization_management_level', group_$_ids,
             vote_$1_ids, poll_voted_$1_ids, poll_voted_$_ids]}
        3:{'collection': 'user', 'ids': [3], 'mapped_fields': ['vote_delegated_$_to_id', 'is_present_in_meeting_ids', 'vote_$_ids', 'vote_delegated_$1_to_id', 'meta_position', 'vote_delegated_vote_$1_ids', 'vote_delegated_vote_$_ids', 'group_$1_ids', 'organization_management_level', ...]}
        3:{'collection': 'user', 'ids': [4], 'mapped_fields': ['vote_delegated_$_to_id', 'is_present_in_meeting_ids', 'vote_$_ids', 'vote_delegated_$1_to_id', 'meta_position', 'vote_delegated_vote_$1_ids', 'vote_delegated_vote_$_ids', 'group_$1_ids', 'organization_management_level', ...]}
        """

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
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
