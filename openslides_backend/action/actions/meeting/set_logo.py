from typing import Any, Dict

from ....models.models import Meeting
from ....shared.exceptions import ActionException
from ....shared.patterns import Collection, FullQualifiedId
from ....shared.schema import required_id_schema
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("meeting.set_logo")
class MeetingSetLogoAction(UpdateAction):
    """
    Action to set a mediafile as logo.
    """

    model = Meeting()
    schema = DefaultSchema(Meeting()).get_update_schema(
        additional_required_fields={
            "place": {"type": "string", "minLength": 1},
            "mediafile_id": required_id_schema,
        },
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Checks is_directory and mimetype and sets logo.
        """
        mediafile = self.datastore.get(
            FullQualifiedId(Collection("mediafile"), instance["mediafile_id"]),
            ["is_directory", "mimetype", "meeting_id"],
        )
        place = instance["place"]
        if mediafile.get("is_directory"):
            raise ActionException("Cannot set a directory as logo.")
        if mediafile.get("mimetype") not in ["image/png", "image/jpeg", "image/gif"]:
            raise ActionException("Cannot set a non image as logo.")
        instance[f"logo_${place}_id"] = instance["mediafile_id"]
        del instance["place"]
        del instance["mediafile_id"]
        return instance
