from ....models.models import PollBallotUser
from ...generics.delete import DeleteAction
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("poll_ballot_user.delete", action_type=ActionType.BACKEND_INTERNAL)
class PollBallotUserDelete(DeleteAction):
    """
    Action to delete a poll_ballot_user.
    """

    model = PollBallotUser()
    schema = DefaultSchema(PollBallotUser()).get_delete_schema()
