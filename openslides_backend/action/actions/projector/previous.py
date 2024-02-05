from typing import Any

from ....models.models import Projector
from ....permissions.permissions import Permissions
from ....services.datastore.commands import GetManyRequest
from ....shared.filters import And, FilterOperator
from ....shared.patterns import fqid_from_collection_and_id
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from ..projection.update import ProjectionUpdate


@register_action("projector.previous")
class ProjectorPrevious(UpdateAction):
    """
    Action to get to the next projection.
    """

    model = Projector()
    schema = DefaultSchema(Projector()).get_update_schema()
    permission = Permissions.Projector.CAN_MANAGE

    def get_updated_instances(self, payload: ActionData) -> ActionData:
        for instance in payload:
            projector = self.datastore.get(
                fqid_from_collection_and_id(self.model.collection, instance["id"]),
                [
                    "current_projection_ids",
                    "preview_projection_ids",
                    "history_projection_ids",
                    "meeting_id",
                ],
            )

            # check if there are history projections
            if not projector.get("history_projection_ids"):
                continue

            # move unstable current projections into preview
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
            transfer_to_preview_projection_ids = [
                projection["id"]
                for projection in current_projections
                if not self.is_stable(projection)
            ]
            new_preview_projection_ids = (
                transfer_to_preview_projection_ids
                + projector.get("preview_projection_ids", [])
            )
            self.set_weight_to_projection(
                transfer_to_preview_projection_ids,
                projector["meeting_id"],
                instance["id"],
            )

            # move highest history projection to current
            new_current_projection_id = self.get_max_history_projection(projector)
            new_current_projection_ids = [
                new_current_projection_id
            ] + new_current_projection_ids
            new_history_projection_ids = [
                id_
                for id_ in projector["history_projection_ids"]
                if id_ != new_current_projection_id
            ]

            # set projections and run update.
            instance["current_projection_ids"] = new_current_projection_ids
            instance["preview_projection_ids"] = new_preview_projection_ids
            instance["history_projection_ids"] = new_history_projection_ids
            yield instance

    def is_stable(self, value: dict[str, Any]) -> bool:
        return bool(value.get("stable"))

    def get_min_projection_weight(self, meeting_id: int, projector_id: int) -> int:
        filter_ = And(
            FilterOperator("meeting_id", "=", meeting_id),
            FilterOperator("preview_projector_id", "=", projector_id),
        )
        minimum = self.datastore.min("projection", filter_, "weight")
        if minimum is None:
            minimum = 10000
        return minimum

    def set_weight_to_projection(
        self, projection_ids: list[int], meeting_id: int, projector_id: int
    ) -> None:
        min_weight = self.get_min_projection_weight(meeting_id, projector_id)
        increment = 1
        payload_set_weight = []
        for projection_id in projection_ids:
            payload_set_weight.append(
                {"id": projection_id, "weight": min_weight - increment}
            )
            increment += 1
        self.execute_other_action(ProjectionUpdate, payload_set_weight)

    def get_max_history_projection(self, projector: dict[str, Any]) -> int:
        gmr2 = GetManyRequest(
            "projection",
            projector["history_projection_ids"],
            ["id", "weight"],
        )
        result = self.datastore.get_many([gmr2])
        history_projections = list(result.get("projection", {}).values())
        pivot = history_projections[0]
        for projection in history_projections:
            if pivot.get("weight", 10000) < projection.get("weight", 10000):
                pivot = projection
        return pivot["id"]
