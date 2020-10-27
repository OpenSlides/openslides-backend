from typing import Any, Dict

from ...models.models import Mediafile
from ...shared.exceptions import ActionException
from ...shared.patterns import FullQualifiedId
from ..default_schema import DefaultSchema
from ..generics import UpdateAction
from ..register import register_action


@register_action("mediafile.set_as_logo")
class MediafileSetAsLogoAction(UpdateAction):
    """
    Action to set a mediafile as logo.
    """

    model = Mediafile()
    schema = DefaultSchema(Mediafile()).get_update_schema(
        additional_required_fields={"place": {"type": "string"}},
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Checks is_directory and mimetype and sets logo.
        """
        mediafile = self.database.get(
            FullQualifiedId(self.model.collection, instance["id"]),
            ["is_directory", "mimetype", "meeting_id"],
        )
        place = instance["place"]
        meeting_id = mediafile["meeting_id"]
        if mediafile.get("is_directory"):
            raise ActionException("Cannot set a directory as logo.")
        if mediafile.get("mimetype") not in ["image/png", "image/jpeg", "image/gif"]:
            raise ActionException("Cannot set a non image as logo.")
        instance[f"used_as_logo_${place}_in_meeting_id"] = meeting_id
        del instance["place"]
        return instance
