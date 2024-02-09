import time
from typing import Any

from openslides_backend.shared.typing import HistoryInformation

from ....models.models import Motion
from ....permissions.permissions import Permissions
from ....shared.exceptions import ActionException
from ....shared.patterns import fqid_from_collection_and_id
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .motion_state_history_information_mixin import MotionStateHistoryInformationMixin


@register_action("motion.set_recommendation")
class MotionSetRecommendationAction(UpdateAction, MotionStateHistoryInformationMixin):
    """
    Set a recommendation in a motion.
    """

    model = Motion()
    schema = DefaultSchema(Motion()).get_update_schema(["recommendation_id"])
    permission = Permissions.Motion.CAN_MANAGE_METADATA

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        """
        Check recommendation workflow_id and recommendation_label.
        """
        motion = self.datastore.get(
            fqid_from_collection_and_id("motion", instance["id"]), ["state_id"]
        )
        current_state = self.datastore.get(
            fqid_from_collection_and_id("motion_state", motion["state_id"]),
            ["workflow_id"],
        )
        recommendation_state = self.datastore.get(
            fqid_from_collection_and_id("motion_state", instance["recommendation_id"]),
            ["workflow_id", "recommendation_label"],
        )
        if current_state.get("workflow_id") != recommendation_state.get("workflow_id"):
            raise ActionException(
                "Cannot set recommendation. State is from a different workflow as motion."
            )
        if recommendation_state.get("recommendation_label") is None:
            raise ActionException(
                "Recommendation label of a recommendation must be set."
            )
        instance["last_modified"] = round(time.time())
        return instance

    def get_history_information(self) -> HistoryInformation | None:
        return self._get_state_history_information(
            "recommendation_id", "Recommendation"
        )
