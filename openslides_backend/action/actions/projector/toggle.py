from typing import Any

from ....models.models import Projection, Projector
from ....permissions.permissions import Permissions
from ....shared.filters import And, FilterOperator
from ....shared.patterns import fqid_from_collection_and_id
from ....shared.schema import required_id_schema
from ...generics.update import UpdateAction
from ...mixins.weight_mixin import WeightMixin
from ...util.assert_belongs_to_meeting import assert_belongs_to_meeting
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from ..projection.create import ProjectionCreate
from ..projection.delete import ProjectionDelete
from ..projection.update import ProjectionUpdate


@register_action("projector.toggle")
class ProjectorToggle(WeightMixin, UpdateAction):
    """
    Action to toggle projections.
    """

    model = Projector()
    schema = DefaultSchema(Projection()).get_default_schema(
        title="Projector toggle stable schema",
        required_properties=["content_object_id", "meeting_id"],
        optional_properties=["options", "type", "stable"],
        additional_required_fields={
            "ids": {
                "type": "array",
                "items": required_id_schema,
                "uniqueItems": True,
                "minItems": 1,
            },
        },
    )
    permission = Permissions.Projector.CAN_MANAGE

    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        for instance in action_data:
            # check meeting ids from projector ids and content_object
            meeting_id = instance["meeting_id"]
            fqid_content_object = instance["content_object_id"]
            assert_belongs_to_meeting(
                self.datastore,
                [fqid_content_object]
                + [
                    fqid_from_collection_and_id("projector", id)
                    for id in instance["ids"]
                ],
                meeting_id,
            )

            for projector_id in instance["ids"]:
                stable = instance.get("stable", False)
                filter_ = And(
                    FilterOperator("current_projector_id", "=", projector_id),
                    FilterOperator(
                        "content_object_id", "=", instance["content_object_id"]
                    ),
                    FilterOperator("stable", "=", stable),
                    FilterOperator("meeting_id", "=", meeting_id),
                )
                if instance.get("type"):
                    filter_ = And(
                        filter_, FilterOperator("type", "=", instance["type"])
                    )
                result = self.datastore.filter("projection", filter_, ["id"])
                if result:
                    projection_ids = [id_ for id_ in result]
                    if stable:
                        self.execute_other_action(
                            ProjectionDelete, [{"id": id_} for id_ in projection_ids]
                        )
                    else:
                        self.move_projections_to_history(
                            meeting_id, projector_id, projection_ids
                        )
                else:
                    data: dict[str, Any] = {
                        "current_projector_id": projector_id,
                        "stable": stable,
                        "type": instance.get("type"),
                        "content_object_id": instance["content_object_id"],
                        "options": instance.get("options"),
                        "meeting_id": meeting_id,
                    }
                    if not stable:
                        self.move_all_unstable_projections_to_history(
                            meeting_id, projector_id
                        )
                        yield {"id": projector_id, "scroll": 0}
                    self.execute_other_action(ProjectionCreate, [data])

    def move_projections_to_history(
        self, meeting_id: int, projector_id: int, projection_ids: list[int]
    ) -> None:
        filter_ = And(
            FilterOperator("meeting_id", "=", meeting_id),
            FilterOperator("history_projector_id", "=", projector_id),
        )
        weight = self.get_weight(filter_, "projection")
        self.execute_other_action(
            ProjectionUpdate,
            [
                {
                    "id": int(projection_id),
                    "current_projector_id": None,
                    "history_projector_id": projector_id,
                    "weight": weight + i,
                }
                for i, projection_id in enumerate(projection_ids)
            ],
        )

    def move_all_unstable_projections_to_history(
        self, meeting_id: int, projector_id: int
    ) -> None:
        filter_ = And(
            FilterOperator("meeting_id", "=", meeting_id),
            FilterOperator("current_projector_id", "=", projector_id),
            FilterOperator("stable", "=", False),
        )
        result = self.datastore.filter("projection", filter_, ["id"])
        if result:
            self.move_projections_to_history(
                meeting_id, projector_id, [int(id_) for id_ in result]
            )
