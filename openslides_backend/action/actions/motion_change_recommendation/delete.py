from openslides_backend.action.mixins.extend_history_mixin import ExtendHistoryMixin

from ....models.models import MotionChangeRecommendation
from ....permissions.permissions import Permissions
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("motion_change_recommendation.delete")
class MotionChangeRecommendationDeleteAction(ExtendHistoryMixin, DeleteAction):
    model = MotionChangeRecommendation()
    schema = DefaultSchema(MotionChangeRecommendation()).get_delete_schema()
    permission = Permissions.Motion.CAN_MANAGE
    history_information = "Motion change recommendation deleted"
    history_relation_field = "motion_id"
    extend_history_to = "motion_id"
