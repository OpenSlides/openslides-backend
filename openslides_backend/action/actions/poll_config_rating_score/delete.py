from ....models.models import PollConfigRatingScore
from ...generics.delete import DeleteAction
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action(
    "poll_config_rating_score.delete", action_type=ActionType.BACKEND_INTERNAL
)
class PollConfigRatingScoreDelete(DeleteAction):
    """
    Action to delete a poll_config_rating_score.
    """

    model = PollConfigRatingScore()
    schema = DefaultSchema(PollConfigRatingScore()).get_delete_schema()
