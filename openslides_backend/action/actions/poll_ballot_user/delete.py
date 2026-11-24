from ....models.models import PollBallotUser
from ...generics.delete_poll_collection import PollCollectionDeleteAction
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("poll_ballot_user.delete", action_type=ActionType.BACKEND_INTERNAL)
class PollBallotUserDelete(PollCollectionDeleteAction):
    """
    Action to delete a poll_ballot_user.
    """

    model = PollBallotUser()
    schema = DefaultSchema(PollBallotUser()).get_delete_schema()
