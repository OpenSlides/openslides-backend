import time
from typing import Any, Dict

from ...models.models import Motion
from ...shared.patterns import Collection, FullQualifiedId
from ...shared.schema import optional_id_schema
from ..default_schema import DefaultSchema
from ..generics import UpdateAction
from ..register import register_action


@register_action("motion.update_metadata")
class MotionUpdateMetadata(UpdateAction):
    """
    Action to update motion metadata.
    """

    model = Motion()
    schema = DefaultSchema(Motion()).get_update_schema(
        optional_properties=[
            "state_extension",
            "recommendation_extension",
            "category_id",
            "block_id",
            "supporter_ids",
            "tag_ids",
            "attachment_ids",
        ],
        additional_optional_fields={"workflow_id": optional_id_schema},
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        if instance.get("workflow_id"):
            motion = self.datastore.get(
                FullQualifiedId(self.model.collection, instance["id"]), ["state_id"]
            )
            state = self.datastore.get(
                FullQualifiedId(Collection("motion_state"), motion["state_id"]),
                ["workflow_id"],
            )
            if instance["workflow_id"] != state.get("workflow_id"):
                workflow = self.datastore.get(
                    FullQualifiedId(
                        Collection("motion_workflow"), instance["workflow_id"]
                    ),
                    ["first_state_id"],
                )
                instance["state_id"] = workflow["first_state_id"]
                instance["recommendation_id"] = None
        instance["last_modified"] = round(time.time())
        return instance
