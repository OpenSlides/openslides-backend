from typing import Any

from ....models.models import Projector
from ....permissions.permissions import Permissions
from ....services.database.commands import GetManyRequest
from ....shared.filters import And, FilterOperator
from ....shared.patterns import fqid_from_collection_and_id
from ...generics.update import UpdateAction
from ...mixins.weight_mixin import WeightMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from ..projection.update import ProjectionUpdate


@register_action("projector.next")
class ProjectorNext(WeightMixin, UpdateAction):
    """
    Action to get to the next projection.
    """

    model = Projector()
    schema = DefaultSchema(Projector()).get_update_schema()
    permission = Permissions.Projector.CAN_MANAGE

    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        for instance in action_data:
            projector = self.datastore.get(
                fqid_from_collection_and_id(self.model.collection, instance["id"]),
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
                    "projection",
                    projector["current_projection_ids"],
                    ["id", "stable"],
                )
                result = self.datastore.get_many([gmr])
                current_projections = list(result.get("projection", {}).values())
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

    def is_stable(self, value: dict[str, Any]) -> bool:
        return bool(value.get("stable"))

    def set_weight_to_projection(
        self, projection_ids: list[int], meeting_id: int, projector_id: int
    ) -> None:
        filter = And(
            FilterOperator("meeting_id", "=", meeting_id),
            FilterOperator("history_projector_id", "=", projector_id),
        )
        weight = self.get_weight(filter, "projection")
        action_data = []
        for i, projection_id in enumerate(projection_ids):
            action_data.append({"id": projection_id, "weight": weight + i})
        self.execute_other_action(ProjectionUpdate, action_data)

    def get_min_preview_projection(self, projector: dict[str, Any]) -> int:
        gmr2 = GetManyRequest(
            "projection",
            projector["preview_projection_ids"],
            ["id", "weight"],
        )
        result = self.datastore.get_many([gmr2])
        preview_projections = list(result.get("projection", {}).values())
        pivot = preview_projections[0]
        for projection in preview_projections:
            if pivot.get("weight", 10000) > projection.get("weight", 10000):
                pivot = projection
        return pivot["id"]
