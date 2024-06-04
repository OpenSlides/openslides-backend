from typing import Any

from ....models.models import Projection, Projector
from ....permissions.permissions import Permissions
from ....shared.filters import And, FilterOperator
from ....shared.patterns import fqid_from_collection_and_id
from ....shared.schema import id_list_schema, optional_str_schema
from ...generics.update import UpdateAction
from ...mixins.singular_action_mixin import SingularActionMixin
from ...mixins.weight_mixin import WeightMixin
from ...util.assert_belongs_to_meeting import assert_belongs_to_meeting
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from ..projection.create import ProjectionCreate
from ..projection.delete import ProjectionDelete
from ..projection.update import ProjectionUpdate


@register_action("projector.project")
class ProjectorProject(WeightMixin, SingularActionMixin, UpdateAction):
    """
    Action to projector project.
    """

    model = Projector()
    schema = DefaultSchema(Projection()).get_default_schema(
        required_properties=["content_object_id", "meeting_id"],
        optional_properties=["options", "stable", "type"],
        additional_required_fields={
            "ids": id_list_schema,
        },
        additional_optional_fields={
            "mode": optional_str_schema
        },
        title="Projector project schema",
    )
    permission = Permissions.Projector.CAN_MANAGE

    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        action_data = super().get_updated_instances(action_data)
        for instance in action_data:
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

            self.move_equal_projections_to_history_or_unset(instance, meeting_id)
            if not instance.get("stable"):
                self.move_unstable_projections_to_history(instance)

            create_data = []
            for projector_id in instance["ids"]:
                data_dict = {
                    "current_projector_id": projector_id,
                    "meeting_id": meeting_id,
                    "content_object_id": instance["content_object_id"],
                }
                for field in ("options", "stable", "type"):
                    if field in instance:
                        data_dict[field] = instance[field]
                create_data.append(data_dict)
            if create_data:
                self.execute_other_action(ProjectionCreate, create_data)
            if not instance.get("stable"):
                for projector_id in instance["ids"]:
                    yield {"id": projector_id, "scroll": 0}

    def move_equal_projections_to_history_or_unset(
        self, instance: dict[str, Any], meeting_id: int
    ) -> None:
        filter_ = And(
            FilterOperator("meeting_id", "=", meeting_id),
            FilterOperator("content_object_id", "=", instance["content_object_id"]),
            FilterOperator("stable", "=", instance.get("stable", False)),
            FilterOperator("type", "=", instance.get("type")),
        )
        result = self.datastore.filter(
            "projection",
            filter_,
            ["id", "current_projector_id", "stable", "meeting_id"],
        )
        for projection_id in result:
            if result[projection_id]["current_projector_id"]:
                if instance.get("mode") != "UPDATE_ONLY_SELECTED" or result[projection_id]["current_projector_id"] in instance["ids"]:
                    # Unset stable equal projections
                    if result[projection_id]["stable"]:
                        action_del_data = [{"id": int(projection_id)}]
                        self.execute_other_action(ProjectionDelete, action_del_data)
                    # Move unstable equal projections to history
                    else:
                        filter_ = And(
                            FilterOperator(
                                "meeting_id", "=", result[projection_id]["meeting_id"]
                            ),
                            FilterOperator(
                                "history_projector_id",
                                "=",
                                result[projection_id]["current_projector_id"],
                            ),
                        )
                        weight = self.get_weight(filter_, "projection")
                        action_data = [
                            {
                                "id": int(projection_id),
                                "current_projector_id": None,
                                "history_projector_id": result[projection_id][
                                    "current_projector_id"
                                ],
                                "weight": weight,
                            }
                        ]
                        self.execute_other_action(ProjectionUpdate, action_data)

    def move_unstable_projections_to_history(self, instance: dict[str, Any]) -> None:
        for projector_id in instance["ids"]:
            filter_ = And(
                FilterOperator("meeting_id", "=", instance["meeting_id"]),
                FilterOperator("current_projector_id", "=", projector_id),
                FilterOperator("stable", "=", False),
            )
            projections = self.datastore.filter("projection", filter_, ["id"])
            filter_ = And(
                FilterOperator("meeting_id", "=", instance["meeting_id"]),
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
                    for i, projection_id in enumerate(projections)
                ],
            )
