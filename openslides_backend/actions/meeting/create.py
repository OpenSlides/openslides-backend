from typing import Any

import fastjsonschema  # type: ignore

from ...models.meeting import Meeting
from ...shared.exceptions import PermissionDenied
from ...shared.interfaces import Event, WriteRequestElement
from ...shared.patterns import FullQualifiedField, FullQualifiedId
from ...shared.permissions.meeting import MEETING_CAN_MANAGE
from ...shared.schema import schema_version
from ..actions import register_action
from ..actions_interface import Payload
from ..base import Action, DataSet

create_meeting_schema = fastjsonschema.compile(
    {
        "$schema": schema_version,
        "title": "New meetings schema",
        "description": "An array of new meetings.",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "committee_id": Meeting().get_schema("committee_id"),
                "title": Meeting().get_schema("title"),
            },
            "required": ["committee_id", "title"],
        },
        "minItems": 1,
        "uniqueItems": True,
    }
)


@register_action("meeting.create")
class MeetingCreate(Action):
    """
    Action to create meetings.
    """

    model = Meeting()
    schema = create_meeting_schema

    def check_permission(self, committee_id: int) -> None:
        required_permission = f"{committee_id}/{MEETING_CAN_MANAGE}"
        if not self.permission.has_perm(self.user_id, required_permission):
            raise PermissionDenied(
                f"User does not have {MEETING_CAN_MANAGE} permission for committee {committee_id}."
            )

    def prepare_dataset(self, payload: Payload) -> DataSet:
        data = []
        for meeting in payload:
            self.check_permission(meeting["committee_id"])
            id, position = self.database.getId(collection=self.model.collection)
            self.set_min_position(position)
            references = self.get_references(
                model=self.model, id=id, obj=meeting, fields=["committee_id"],
            )
            data.append({"meeting": meeting, "new_id": id, "references": references})
        return {"position": self.position, "data": data}

    def create_instance_write_request_element(
        self, position: int, element: Any
    ) -> WriteRequestElement:
        fqfields = {}

        # Committee
        fqfields[
            FullQualifiedField(self.model.collection, element["new_id"], "committee_id")
        ] = element["meeting"]["committee_id"]

        # Title
        fqfields[
            FullQualifiedField(self.model.collection, element["new_id"], "title")
        ] = element["meeting"]["title"]

        information = {
            FullQualifiedId(self.model.collection, element["new_id"]): [
                "Meeting created"
            ]
        }
        event = Event(type="create", fqfields=fqfields)
        return WriteRequestElement(
            events=[event],
            information=information,
            user_id=self.user_id,
            locked_fields={},
        )
