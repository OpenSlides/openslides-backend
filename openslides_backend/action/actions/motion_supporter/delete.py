from typing import Any

from ....models.models import MotionSupporter
from ....services.datastore.commands import GetManyRequest
from ....shared.patterns import fqid_from_collection_and_id
from ...mixins.motion_meeting_user_delete import build_motion_meeting_user_delete_action
from ...util.register import register_action
from ...util.typing import ActionData
from .mixins import SupporterActionMixin

BaseClass: type = build_motion_meeting_user_delete_action(MotionSupporter)


@register_action("motion_supporter.delete")
class MotionSupporterDeleteAction(BaseClass, SupporterActionMixin):
    history_information = "Supporters changed"
    history_relation_field = "motion_id"

    def prefetch(self, action_data: ActionData) -> None:
        super().prefetch(action_data)
        if not self.internal:
            self.datastore.get_many(
                [
                    GetManyRequest(
                        "motion_supporter",
                        [payload["id"] for payload in action_data],
                        ["motion_id", "meeting_user_id", "meeting_id"],
                    )
                ]
            )

    def get_motion_id(self, instance: dict[str, Any]) -> int:
        return self.datastore.get(
            fqid_from_collection_and_id("motion_supporter", instance["id"]),
            ["motion_id"],
        )["motion_id"]

    def get_meeting_user_id(self, instance: dict[str, Any]) -> int | None:
        return self.datastore.get(
            fqid_from_collection_and_id("motion_supporter", instance["id"]),
            ["meeting_user_id"],
        ).get("meeting_user_id")

    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        if self.internal:
            return action_data
        return self.check_action_data(action_data)
