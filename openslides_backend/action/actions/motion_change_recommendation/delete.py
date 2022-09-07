from ....models.models import MotionChangeRecommendation
from ....permissions.permissions import Permissions
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("motion_change_recommendation.delete")
class MotionChangeRecommendationDeleteAction(DeleteAction):
    model = MotionChangeRecommendation()
    schema = DefaultSchema(MotionChangeRecommendation()).get_delete_schema()
    permission = Permissions.Motion.CAN_MANAGE
    history_information = "Motion change recommendation deleted"
