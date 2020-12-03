from typing import Any, Dict

from ....models.models import Meeting
from ....shared.exceptions import ActionException
from ....shared.patterns import Collection, FullQualifiedId
from ....shared.schema import required_id_schema
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("meeting.set_font")
class MeetingSetFontAction(UpdateAction):
    """
    Action to set a mediafile as font.
    """

    model = Meeting()
    schema = DefaultSchema(Meeting()).get_update_schema(
        additional_required_fields={
            "place": {"type": "string", "minLength": 1},
            "mediafile_id": required_id_schema,
        }
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Checks is_directory and mimetype and sets font.
        """
        mediafile = self.datastore.get(
            FullQualifiedId(Collection("mediafile"), instance["mediafile_id"]),
            ["is_directory", "mimetype", "meeting_id"],
        )
        place = instance["place"]
        if mediafile.get("is_directory"):
            raise ActionException("Cannot set a directory as font.")
        if mediafile.get("mimetype") not in [
            "font/ttf",
            "font/woff",
            "application/font-woff",
            "application/font-sfnt",
        ]:
            raise ActionException("Cannot set a non font as font.")
        instance[f"font_${place}_id"] = instance["mediafile_id"]
        del instance["place"]
        del instance["mediafile_id"]
        return instance
