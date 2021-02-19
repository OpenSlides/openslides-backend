from typing import Any, Dict

from ....models.models import Projector
from ....shared.exceptions import ActionException
from ....shared.patterns import FullQualifiedId
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("projector.delete")
class ProjectorDelete(DeleteAction):
    """
    Action to delete a projector.
    """

    model = Projector()
    schema = DefaultSchema(Projector()).get_delete_schema()

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        projector = self.datastore.get(
            FullQualifiedId(self.model.collection, instance["id"]),
            ["used_as_reference_projector_meeting_id"],
        )
        if projector.get("used_as_reference_projector_meeting_id"):
            raise ActionException(
                "A used as reference projector is not allowed to delete."
            )
        return instance
