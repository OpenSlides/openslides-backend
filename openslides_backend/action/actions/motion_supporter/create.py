from typing import Any

from ....models.models import MotionSupporter
from ...mixins.motion_meeting_user_create import build_motion_meeting_user_create_action
from ...util.register import register_action
from .mixins import SupporterActionMixin

BaseClass: type = build_motion_meeting_user_create_action(
    MotionSupporter, True, with_weight=False
)


@register_action("motion_supporter.create")
class MotionSupporterCreateAction(BaseClass, SupporterActionMixin):
    history_information = "Supporters changed"
    history_relation_field = "motion_id"

    def get_motion_id(self, instance: dict[str, Any]) -> int:
        return instance["motion_id"]

    def get_meeting_user_id(self, instance: dict[str, Any]) -> int | None:
        return instance["meeting_user_id"]
