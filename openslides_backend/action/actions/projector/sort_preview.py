from typing import Any, Dict

from ....models.models import Projector
from ....permissions.permissions import Permissions
from ....shared.exceptions import ActionException
from ....shared.patterns import FullQualifiedId
from ....shared.schema import required_id_schema
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from ..projection.update import ProjectionUpdate


@register_action("projector.sort_preview")
class ProjectorSortPreview(UpdateAction):
    """
    Action to sort preview of a projector.
    """

    model = Projector()
    schema = DefaultSchema(Projector()).get_update_schema(
        additional_required_fields={
            "projection_ids": {"type": "array", "items": required_id_schema}
        },
    )
    permission = Permissions.Projector.CAN_MANAGE

    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        for instance in action_data:
            self.check_preview_ids(instance)

            weight = 1
            for projection_id in instance["projection_ids"]:
                self.execute_other_action(
                    ProjectionUpdate, [{"id": projection_id, "weight": weight}]
                )
                weight += 1
        return []

    def check_preview_ids(self, instance: Dict[str, Any]) -> None:
        projector = self.datastore.get(
            FullQualifiedId(self.model.collection, instance["id"]),
            ["preview_projection_ids"],
        )
        if set(instance["projection_ids"]) != set(
            projector.get("preview_projection_ids", [])
        ):
            raise ActionException(
                "Must give all preview projections of this projector and nothing else."
            )
