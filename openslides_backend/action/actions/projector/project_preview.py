from typing import Any

from ....models.models import Projection, Projector
from ....permissions.permissions import Permissions
from ....services.datastore.commands import GetManyRequest
from ....shared.exceptions import ActionException
from ....shared.filters import And, FilterOperator
from ....shared.patterns import fqid_from_collection_and_id
from ...generics.update import UpdateAction
from ...mixins.weight_mixin import WeightMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ..projection.update import ProjectionUpdate


@register_action("projector.project_preview")
class ProjectorProjectPreview(WeightMixin, UpdateAction):
    """
    Action to get to the next projection.
    """

    model = Projector()
    schema = DefaultSchema(Projection()).get_update_schema()
    permission_model = Projection()
    permission = Permissions.Projector.CAN_MANAGE

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        projection_id = instance.pop("id")
        projection = self.datastore.get(
            fqid_from_collection_and_id("projection", projection_id),
            ["preview_projector_id"],
        )
        # check if projection is from a preview projector
        if not projection.get("preview_projector_id"):
            raise ActionException("Projection has not a preview_projector_id.")
        projector_id = projection["preview_projector_id"]
        projector = self.datastore.get(
            fqid_from_collection_and_id(self.model.collection, projector_id),
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
            projector_id,
        )
        new_current_projection_ids += [projection_id]
        new_preview_projection_ids = [
            id_ for id_ in projector["preview_projection_ids"] if id_ != projection_id
        ]
        instance["id"] = projector_id
        instance["current_projection_ids"] = new_current_projection_ids
        instance["preview_projection_ids"] = new_preview_projection_ids
        instance["history_projection_ids"] = new_history_projection_ids
        return instance

    def is_stable(self, value: dict[str, Any]) -> bool:
        return value.get("stable", False)

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
