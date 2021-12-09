from ....models.models import Projection, Projector
from ....permissions.permissions import Permissions
from ....shared.filters import And, FilterOperator
from ....shared.patterns import Collection
from ....shared.schema import required_id_schema
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from ..projection.create import ProjectionCreate


@register_action("projector.add_to_preview")
class ProjectorAddToPreview(UpdateAction):
    """
    Action to projector project.
    """

    model = Projector()
    schema = DefaultSchema(Projection()).get_default_schema(
        required_properties=["content_object_id", "meeting_id"],
        optional_properties=["options", "stable", "type"],
        additional_required_fields={
            "ids": {"type": "array", "items": required_id_schema, "uniqueItems": True}
        },
        title="Projector add to preview schema",
    )
    permission = Permissions.Projector.CAN_MANAGE

    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        for instance in action_data:
            # add the preview projections
            for projector_id in instance["ids"]:
                max_weight = self.get_max_projection_weight(projector_id, meeting_id)
                data = {
                    "meeting_id": instance["meeting_id"],
                    "preview_projector_id": projector_id,
                    "weight": max_weight + 1,
                    "content_object_id": instance["content_object_id"],
                }
                for field in ("options", "stable", "type"):
                    if instance.get(field):
                        data[field] = instance[field]
                self.execute_other_action(ProjectionCreate, [data])
        return []

    def get_max_projection_weight(self, projector_id: int, meeting_id: int) -> int:
        filter_ = And(
            FilterOperator("preview_projector_id", "=", projector_id),
            FilterOperator("meeting_id", "=", meeting_id),
        )
        return self.datastore.max(Collection("projection"), filter_, "weight") or 0
