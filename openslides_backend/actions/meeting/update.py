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

update_meeting_schema = fastjsonschema.compile(
    {
        "$schema": schema_version,
        "title": "Update meetings schema",
        "description": "An array of meetings to be updated.",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "id": Meeting().get_schema("id"),
                "title": Meeting().get_schema("title"),
            },
            "required": ["id"],
        },
        "minItems": 1,
        "uniqueItems": True,
    }
)


@register_action("meeting.update")
class MeetingUpdate(Action):
    """
    Action to update meetings.
    """

    model = Meeting()
    schema = update_meeting_schema

    def check_permission(self, committee_id: int) -> None:
        required_permission = f"{committee_id}/{MEETING_CAN_MANAGE}"
        if not self.permission.has_perm(self.user_id, required_permission):
            raise PermissionDenied(
                f"User does not have {MEETING_CAN_MANAGE} permission for committee {committee_id}."
            )

    def prepare_dataset(self, payload: Payload) -> DataSet:
        data = []
        for meeting in payload:
            db_meeting, position = self.database.get(
                fqid=FullQualifiedId(self.model.collection, id=meeting["id"]),
                mapped_fields=["committee_id"],
            )
            self.set_min_position(position)
            self.check_permission(db_meeting["committee_id"])
            references = self.get_references(
                model=self.model,
                id=meeting["id"],
                obj=meeting,
                field_names=[],
                deletion_possible=True,
            )
            data.append({"meeting": meeting, "references": references})
        return {"position": self.position, "data": data}

    def create_instance_write_request_element(
        self, position: int, element: Any
    ) -> WriteRequestElement:
        fqfields = {}
        for field in element["meeting"].keys():
            if field == "id":
                continue
            fqfields[
                FullQualifiedField(
                    self.model.collection, element["meeting"]["id"], field
                )
            ] = element["meeting"][field]
        information = {
            FullQualifiedId(self.model.collection, element["meeting"]["id"]): [
                "Meeting updated"
            ]
        }
        event = Event(type="update", fqfields=fqfields)
        return WriteRequestElement(
            events=[event],
            information=information,
            user_id=self.user_id,
            locked_fields={
                FullQualifiedField(
                    self.model.collection, element["meeting"]["id"], "deleted"
                ): position
            },
        )
