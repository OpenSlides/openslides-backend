from typing import Any, Dict, List

from ....models.models import Projector
from ....services.datastore.commands import GetManyRequest
from ....shared.filters import And, FilterOperator
from ....shared.patterns import Collection, FullQualifiedId
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from ..projection.set_weight import ProjectionSetWeight


@register_action("projector.next")
class ProjectorNext(UpdateAction):
    """
    Action to get to the next projection.
    """

    model = Projector()
    schema = DefaultSchema(Projector()).get_update_schema()

    def get_updated_instances(self, payload: ActionData) -> ActionData:
        for instance in payload:
            projector = self.datastore.get(
                FullQualifiedId(self.model.collection, instance["id"]),
                [
                    "current_projection_ids",
                    "preview_projection_ids",
                    "history_projection_ids",
                    "meeting_id",
                ],
            )
            if not projector.get("preview_projection_ids"):
                continue
            current_projections = []
            if projector.get("current_projection_ids"):
                gmr = GetManyRequest(
                    Collection("projection"),
                    projector["current_projection_ids"],
                    ["id", "stable"],
                )
                result = self.datastore.get_many([gmr])
                current_projections = list(
                    result.get(Collection("projection"), {}).values()
                )
            new_current_projection_ids = [
                projection["id"]
                for projection in current_projections
                if self.is_stable(projection)
            ]
            transfer_to_history_projection_ids = [
                projection["id"]
                for projection in current_projections
                if not self.is_stable(projection)
            ]
            new_history_projection_ids = (
                projector.get("history_projection_ids", [])
                + transfer_to_history_projection_ids
            )
            self.set_weight_to_projection(
                transfer_to_history_projection_ids,
                projector["meeting_id"],
                instance["id"],
            )
            new_current_projection_id = self.get_min_preview_projection(projector)
            new_current_projection_ids += [new_current_projection_id]
            new_preview_projection_ids = [
                id_
                for id_ in projector["preview_projection_ids"]
                if id_ != new_current_projection_id
            ]
            instance["current_projection_ids"] = new_current_projection_ids
            instance["preview_projection_ids"] = new_preview_projection_ids
            instance["history_projection_ids"] = new_history_projection_ids
            yield instance

    def is_stable(self, value: Dict[str, Any]) -> bool:
        return bool(value.get("stable"))

    def get_max_projection_weight(self, meeting_id: int, projector_id: int) -> int:
        filter_ = And(
            FilterOperator("meeting_id", "=", meeting_id),
            FilterOperator("history_projector_id", "=", projector_id),
        )
        maximum = self.datastore.max(Collection("projection"), filter_, "weight", "int")
        if maximum is None:
            maximum = 1
        return maximum

    def set_weight_to_projection(
        self, projection_ids: List[int], meeting_id: int, projector_id: int
    ) -> None:
        max_weight = self.get_max_projection_weight(meeting_id, projector_id)
        increment = 1
        payload_set_weight = []
        for projection_id in projection_ids:
            payload_set_weight.append(
                {"id": projection_id, "weight": max_weight + increment}
            )
            increment += 1
        self.execute_other_action(ProjectionSetWeight, payload_set_weight)

    def get_min_preview_projection(self, projector: Dict[str, Any]) -> int:
        gmr2 = GetManyRequest(
            Collection("projection"),
            projector["preview_projection_ids"],
            ["id", "weight"],
        )
        result = self.datastore.get_many([gmr2])
        preview_projections = list(result.get(Collection("projection"), {}).values())
        pivot = preview_projections[0]
        for projection in preview_projections:
            if pivot.get("weight", 10000) > projection.get("weight", 10000):
                pivot = projection
        return pivot["id"]
