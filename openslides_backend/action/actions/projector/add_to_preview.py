from ....models.models import Projection, Projector
from ....permissions.permissions import Permissions
from ....shared.filters import And, FilterOperator
from ....shared.schema import id_list_schema
from ...generics.update import UpdateAction
from ...mixins.weight_mixin import WeightMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from ..projection.create import ProjectionCreate


@register_action("projector.add_to_preview")
class ProjectorAddToPreview(WeightMixin, UpdateAction):
    """
    Action to projector project.
    """

    model = Projector()
    schema = DefaultSchema(Projection()).get_default_schema(
        required_properties=["content_object_id", "meeting_id"],
        optional_properties=["options", "stable", "type"],
        additional_required_fields={"ids": id_list_schema},
        title="Projector add to preview schema",
    )
    permission = Permissions.Projector.CAN_MANAGE

    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        for instance in action_data:
            # add the preview projections
            for projector_id in instance["ids"]:
                filter = And(
                    FilterOperator("preview_projector_id", "=", projector_id),
                    FilterOperator("meeting_id", "=", instance["meeting_id"]),
                )
                weight = self.get_weight(filter, "projection")
                data = {
                    "meeting_id": instance["meeting_id"],
                    "preview_projector_id": projector_id,
                    "weight": weight,
                    "content_object_id": instance["content_object_id"],
                }
                for field in ("options", "stable", "type"):
                    if instance.get(field):
                        data[field] = instance[field]
                self.execute_other_action(ProjectionCreate, [data])
        return []
