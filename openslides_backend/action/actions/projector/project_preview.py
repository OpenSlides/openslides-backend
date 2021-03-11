from typing import Any, Dict, List

from ....models.models import Projection, Projector
from ....services.datastore.commands import GetManyRequest
from ....shared.filters import And, FilterOperator
from ....shared.patterns import Collection, FullQualifiedId
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from ..projection.set_weight import ProjectionSetWeight


@register_action("projector.project_preview")
class ProjectorProjectPreview(UpdateAction):
    """
    Action to get to the next projection.
    """

    model = Projector()
    schema = DefaultSchema(Projection()).get_update_schema()

    def get_updated_instances(self, payload: ActionData) -> ActionData:
        for instance in payload:
            projection_id = instance.pop("id")
            projection = self.datastore.get(
                FullQualifiedId(Collection("projection"), projection_id),
                ["preview_projector_id"],
            )
            # check if projection is from a preview projector
            if not projection.get("preview_projector_id"):
                continue
            projector_id = projection["preview_projector_id"]
            projector = self.datastore.get(
                FullQualifiedId(self.model.collection, projector_id),
                [
                    "current_projection_ids",
                    "preview_projection_ids",
                    "history_projection_ids",
                    "meeting_id",
                ],
            )
            # move current unstable projections to history
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
                projector_id,
            )
            new_current_projection_ids += [projection_id]
            new_preview_projection_ids = [
                id_
                for id_ in projector["preview_projection_ids"]
                if id_ != projection_id
            ]
            instance["id"] = projector_id
            instance["current_projection_ids"] = new_current_projection_ids
            instance["preview_projection_ids"] = new_preview_projection_ids
            instance["history_projection_ids"] = new_history_projection_ids
            yield instance

    def is_stable(self, value: Dict[str, Any]) -> bool:
        return value.get("stable", False)

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
