from typing import Any, Dict

from ....models.models import Projection
from ....permissions.permissions import Permissions
from ....shared.exceptions import ActionException
from ....shared.patterns import FullQualifiedId
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("projection.delete")
class ProjectionDelete(DeleteAction):
    """
    Action to delete a projection.
    """

    model = Projection()
    schema = DefaultSchema(Projection()).get_delete_schema()
    permission = Permissions.Projector.CAN_MANAGE

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        projection = self.datastore.get(
            FullQualifiedId(self.model.collection, instance["id"]),
            ["current_projector_id", "preview_projector_id", "meeting_id"],
        )
        if not (
            projection.get("current_projector_id")
            or projection.get("preview_projector_id")
            or self.is_meeting_deleted(projection.get("meeting_id", 0))
        ):
            raise ActionException(
                f"Projection {instance['id']} must have a current_projector_id or a preview_projector_id."
            )
        return instance
