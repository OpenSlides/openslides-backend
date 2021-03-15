from typing import Any, Dict

from ....models.models import Projection, Projector
from ....shared.filters import And, FilterOperator, Not
from ....shared.patterns import Collection, string_to_fqid
from ....shared.schema import required_id_schema
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from ..projection.create import ProjectionCreate
from ..projection.update import ProjectionUpdate


@register_action("projector.project")
class ProjectorProject(UpdateAction):
    """
    Action to projector project.
    """

    model = Projector()
    schema = DefaultSchema(Projection()).get_default_schema(
        required_properties=["content_object_id"],
        optional_properties=["options", "stable", "type"],
        additional_required_fields={
            "ids": {"type": "array", "items": required_id_schema}
        },
        title="Projector project schema",
    )

    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        for instance in action_data:
            content_object = self.datastore.get(
                string_to_fqid(instance["content_object_id"]), ["meeting_id"]
            )
            meeting_id = content_object["meeting_id"]

            if instance.get("stable", False) is False:
                self.move_equal_projections_to_history(instance, meeting_id)

            create_data = []
            for projector_id in instance["ids"]:
                data_dict = {
                    "current_projector_id": projector_id,
                    "meeting_id": meeting_id,
                }
                for field in ("content_object_id", "options", "stable", "type"):
                    if field in instance:
                        data_dict[field] = instance[field]
                create_data.append(data_dict)
            if create_data:
                self.execute_other_action(ProjectionCreate, create_data)
        return []

    def move_equal_projections_to_history(
        self, instance: Dict[str, Any], meeting_id: int
    ) -> None:
        filter_ = And(
            FilterOperator("meeting_id", "=", meeting_id),
            FilterOperator("content_object_id", "=", instance["content_object_id"]),
            FilterOperator("stable", "=", False),
            FilterOperator("type", "=", None),
            *[Not(FilterOperator("id", "=", id_)) for id_ in instance["ids"]],
        )
        result = self.datastore.filter(
            Collection("projection"), filter_, ["id", "current_projector_id"]
        )
        action_data = []
        for projection_id in result:
            if result[projection_id]["current_projector_id"]:
                action_data.append(
                    {
                        "id": int(projection_id),
                        "current_projector_id": None,
                        "history_projector_id": result[projection_id][
                            "current_projector_id"
                        ],
                    }
                )
        if action_data:
            self.execute_other_action(ProjectionUpdate, action_data)
