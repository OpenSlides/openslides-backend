import fastjsonschema  # type: ignore

from ...models.meeting import Meeting
from ...shared.schema import schema_version
from ..action import register_action
from ..generics import UpdateAction

update_meeting_schema = fastjsonschema.compile(
    {
        "$schema": schema_version,
        "title": "Update meetings schema",
        "description": "An array of meetings to be updated.",
        "type": "array",
        "items": {
            "type": "object",
            "properties": Meeting().get_properties("id", "name"),
            "required": ["id"],
            "additionalProperties": False,
        },
        "minItems": 1,
        "uniqueItems": True,
    }
)


@register_action("meeting.update")
class MeetingUpdate(UpdateAction):
    """
    Action to update meetings.
    """

    model = Meeting()
    schema = update_meeting_schema
