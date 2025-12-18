from typing import Any

from openslides_backend.action.mixins.extend_history_mixin import ExtendHistoryMixin
from openslides_backend.action.util.register import register_action

from ....models.models import MotionChangeRecommendation
from ....permissions.permissions import Permissions
from ....services.database.commands import GetManyRequest
from ....shared.exceptions import ActionException
from ....shared.filters import FilterOperator
from ...action import original_instances
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.typing import ActionData

line_change_fields = ["line_from", "line_to"]


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
            *line_change_fields,
        ]
    )
    permission = Permissions.Motion.CAN_MANAGE
    history_information = "Motion change recommendation updated"
    history_relation_field = "motion_id"
    extend_history_to = "motion_id"

    @original_instances
    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        line_changes = {
            payload["id"]: payload
            for payload in action_data
            if any(field in payload for field in line_change_fields)
        }
        if line_changes:
            line_change_data = self.datastore.get_many(
                [
                    GetManyRequest(
                        "motion_change_recommendation",
                        list(line_changes),
                        ["motion_id", *line_change_fields],
                    )
                ]
            )["motion_change_recommendation"]
            motion_id_to_reco_id_to_payload = {}
            for id_, payload in line_changes.items():
                line_change_data[id_].update(payload)
                motion_id = line_change_data[id_]["motion_id"]
                if motion_id not in motion_id_to_reco_id_to_payload:
                    motion_id_to_reco_id_to_payload[motion_id] = {
                        id_: line_change_data[id_]
                    }
                else:
                    motion_id_to_reco_id_to_payload[motion_id][id_] = line_change_data[
                        id_
                    ]
                if (
                    line_change_data[id_]["line_from"]
                    > line_change_data[id_]["line_to"]
                ):
                    raise ActionException(
                        f"Cannot edit motion_change_recommendation/{id_}: New line span would have its from line after its to line."
                    )
            for motion_id, new_reco_data in motion_id_to_reco_id_to_payload.items():
                motion_reco_data = self.datastore.filter(
                    "motion_change_recommendation",
                    FilterOperator("motion_id", "=", motion_id),
                    line_change_fields,
                )
                motion_reco_data.update(new_reco_data)
                self.check_for_intersections(motion_reco_data)
        return action_data

    def check_for_intersections(
        self, motion_reco_data: dict[int, dict[str, Any]]
    ) -> None:
        sorted_reco_data: list[tuple[int, int, int]] = sorted(
            (reco["line_from"], reco["line_to"], id_)
            for id_, reco in motion_reco_data.items()
        )
        intersections: set[int] = set()
        for i in range(len(sorted_reco_data)):
            from_i, to_i, id_i = sorted_reco_data[i]
            j = i + 1
            while j < len(sorted_reco_data):
                from_j, to_j, id_j = sorted_reco_data[j]
                if to_i < from_j:
                    break
                intersections.update([id_i, id_j])
                j += 1
        if intersections:
            raise ActionException(
                f"Cannot edit motion_change_recommendation: New line spans cause intersections concerning recommendations {intersections}."
            )
