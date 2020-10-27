from typing import Any, Dict

from ...models.models import Mediafile
from ...shared.exceptions import ActionException
from ...shared.patterns import FullQualifiedId
from ..default_schema import DefaultSchema
from ..generics import UpdateAction
from ..register import register_action


@register_action("mediafile.set_as_font")
class MediafileSetAsFontAction(UpdateAction):
    """
    Action to set a mediafile as font.
    """

    model = Mediafile()
    schema = DefaultSchema(Mediafile()).get_update_schema(
        additional_required_fields={"place": {"type": "string"}},
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Checks is_directory and mimetype and sets font.
        """
        mediafile = self.database.get(
            FullQualifiedId(self.model.collection, instance["id"]),
            ["is_directory", "mimetype", "meeting_id"],
        )
        place = instance["place"]
        meeting_id = mediafile["meeting_id"]
        if mediafile.get("is_directory"):
            raise ActionException("Cannot set a directory as font.")
        if mediafile.get("mimetype") not in ["font/otf", "font/ttf"]:
            raise ActionException("Cannot set a non font as font.")
        instance[f"used_as_font_${place}_in_meeting_id"] = meeting_id
        del instance["place"]
        return instance
