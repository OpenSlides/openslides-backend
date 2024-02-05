from typing import Any

from ....models.models import Projection
from ....permissions.permissions import Permissions
from ....shared.exceptions import ActionException
from ....shared.patterns import fqid_from_collection_and_id
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

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        projection = self.datastore.get(
            fqid_from_collection_and_id(self.model.collection, instance["id"]),
            [
                "current_projector_id",
                "preview_projector_id",
                "history_projector_id",
                "content_object_id",
                "meeting_id",
            ],
            lock_result=False,
        )
        if not (
            projection.get("current_projector_id")
            or projection.get("preview_projector_id")
            or self.is_meeting_deleted(projection["meeting_id"])
            or self.is_deleted(projection["content_object_id"])
            or (
                "history_projector_id" in projection
                and self.is_deleted(
                    fqid_from_collection_and_id(
                        "projector", projection["history_projector_id"]
                    )
                )
            )
        ):
            raise ActionException(
                f"Projection {instance['id']} must have a current_projector_id or a preview_projector_id."
            )
        return instance
