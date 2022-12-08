from openslides_backend.action.mixins.extend_history_mixin import ExtendHistoryMixin
from openslides_backend.action.util.register import register_action

from ....models.models import MotionChangeRecommendation
from ....permissions.permissions import Permissions
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema


@register_action("motion_change_recommendation.update")
class MotionChangeRecommendationUpdateAction(ExtendHistoryMixin, UpdateAction):
    """
    Action to update motion change recommendations.
    """

    model = MotionChangeRecommendation()
    schema = DefaultSchema(MotionChangeRecommendation()).get_update_schema(
        optional_properties=[
            "text",
            "rejected",
            "internal",
            "type",
            "other_description",
        ]
    )
    permission = Permissions.Motion.CAN_MANAGE
    history_information = "Motion change recommendation updated"
    history_relation_field = "motion_id"
    extend_history_to = "motion_id"
