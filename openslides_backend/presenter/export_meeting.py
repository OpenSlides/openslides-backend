from typing import Any

import fastjsonschema

from ..action.actions.meeting.export_helper import export_meeting
from ..shared.schema import schema_version
from .base import BasePresenter
from .presenter import register_presenter

export_meeting_schema = fastjsonschema.compile(
    {
        "$schema": schema_version,
        "type": "object",
        "title": "export_meeting",
        "description": "export the meeting with meeting_id",
        "properties": {
            "meeting_id": {"type": "integer"},
        },
        "required": ["meeting_id"],
        "additionalProperties": False,
    }
)


@register_presenter("export_meeting")
class ExportMeeting(BasePresenter):
    """
    Export a meeting
    """

    schema = export_meeting_schema

    def get_result(self) -> Any:
        return {"export": export_meeting(self.datastore, self.data["meeting_id"])}
