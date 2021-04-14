from typing import Any, Dict

from ....models.models import Projection, Projector
from ....permissions.permissions import Permissions
from ....shared.filters import And, FilterOperator
from ....shared.patterns import Collection, FullQualifiedId
from ....shared.schema import required_id_schema
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from ..projection.create import ProjectionCreate
from ..projection.delete import ProjectionDelete


@register_action("projector.toggle_stable")
class ProjectorToggleStable(UpdateAction):
    """
    Action to toggle stable projectors.
    """

    model = Projector()
    schema = DefaultSchema(Projection()).get_default_schema(
        title="Projector toggle stable schema",
        required_properties=["content_object_id"],
        optional_properties=["options", "type"],
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
            for projector_id in instance["ids"]:
                filter_ = And(
                    FilterOperator("current_projector_id", "=", projector_id),
                    FilterOperator(
                        "content_object_id", "=", instance["content_object_id"]
                    ),
                    FilterOperator("type", "=", instance.get("type")),
                    FilterOperator("stable", "=", True),
                )
                results = self.datastore.filter(
                    Collection("projection"), filter_, ["id"]
                )
                if results:
                    for id_ in results:
                        self.execute_other_action(ProjectionDelete, [{"id": id_}])
                else:
                    data: Dict[str, Any] = {
                        "current_projector_id": projector_id,
                        "stable": True,
                        "type": instance.get("type"),
                        "content_object_id": instance["content_object_id"],
                        "options": instance.get("options"),
                        "meeting_id": self.get_meeting_id(instance),
                    }
                    self.execute_other_action(ProjectionCreate, [data])
        return []

    def get_meeting_id(self, instance: Dict[str, Any]) -> int:
        projector = self.datastore.get(
            FullQualifiedId(self.model.collection, instance["ids"][0]), ["meeting_id"]
        )
        return projector["meeting_id"]
