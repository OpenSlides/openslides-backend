from typing import Any, Dict

from ....models.models import Meeting
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("meeting.unset_logo")
class MeetingUnsetLogoAction(UpdateAction):
    """
    Action to unset a logo form a meeting.
    """

    model = Meeting()
    schema = DefaultSchema(Meeting()).get_update_schema(
        additional_required_fields={
            "place": {"type": "string", "minLength": 1},
        },
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        place = instance.pop("place")
        instance["logo_$_id"] = {place: None}
        return instance
