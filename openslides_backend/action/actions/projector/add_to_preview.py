from ....models.models import Projection, Projector
from ....shared.filters import FilterOperator
from ....shared.patterns import Collection, string_to_fqid
from ....shared.schema import required_id_schema
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from ..projection.create import ProjectionCreate


@register_action("projector.add_to_preview")
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
            # check content object and get meeting id.
            content_object = self.datastore.get(
                string_to_fqid(instance["content_object_id"]), ["meeting_id"]
            )
            meeting_id = content_object["meeting_id"]

            # add the preview projections
            for projector_id in instance["ids"]:
                max_weight = self.get_max_projection_weight(projector_id)
                data = {
                    "meeting_id": meeting_id,
                    "preview_projector_id": projector_id,
                    "weight": max_weight + 1,
                }
                for field in ("content_object_id", "options", "stable", "type"):
                    if instance.get(field):
                        data[field] = instance[field]
                self.execute_other_action(ProjectionCreate, [data])
        return []

    def get_max_projection_weight(self, projector_id: int) -> int:
        filter_ = FilterOperator("preview_projector_id", "=", projector_id)
        maximum = self.datastore.max(Collection("projection"), filter_, "weight", "int")
        if maximum is None:
            maximum = 1
        return maximum
