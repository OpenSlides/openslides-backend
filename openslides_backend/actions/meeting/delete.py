from typing import Any

import fastjsonschema  # type: ignore

from ...models.meeting import Meeting
from ...shared.exceptions import ActionException, PermissionDenied
from ...shared.interfaces import Event, WriteRequestElement
from ...shared.patterns import FullQualifiedField, FullQualifiedId
from ...shared.permissions.meeting import MEETING_CAN_MANAGE
from ...shared.schema import schema_version
from ..actions import register_action
from ..actions_interface import Payload
from ..base import Action, DataSet

delete_meeting_schema = fastjsonschema.compile(
    {
        "$schema": schema_version,
        "title": "Delete meetings schema",
        "description": "An array of meetings to be deleted.",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {"id": Meeting().get_schema("id")},
            "required": ["id"],
        },
        "minItems": 1,
        "uniqueItems": True,
    }
)


@register_action("meeting.delete")
class MeetingDelete(Action):
    """
    Action to delete meetings.
    """

    model = Meeting()
    schema = delete_meeting_schema

    def check_permission(self, committee_id: int) -> None:
        required_permission = f"{committee_id}/{MEETING_CAN_MANAGE}"
        if not self.permission.has_perm(self.user_id, required_permission):
            raise PermissionDenied(
                f"User does not have {MEETING_CAN_MANAGE} permission for meeting {committee_id}."
            )

    def prepare_dataset(self, payload: Payload) -> DataSet:
        data = []
        for meeting in payload:
            mapped_fields = ["committee_id"] + [
                back_reference_name
                for back_reference_name, _ in self.model.get_back_references()
            ]
            db_meeting, position = self.database.get(
                fqid=FullQualifiedId(self.model.collection, id=meeting["id"]),
                mapped_fields=mapped_fields,
            )
            self.set_min_position(position)
            self.check_permission(db_meeting["committee_id"])
            meeting["committee_id"] = None
            cascade_delete = {}
            for back_reference_name, back_reference in self.model.get_back_references():
                if back_reference.on_delete == "protect":
                    if db_meeting[back_reference_name]:
                        raise ActionException(
                            f"You are not allowed to delete meeting {meeting['id']} as long as there are some referenced objects (see {back_reference_name})."
                        )
                else:
                    # back_reference.on_delete == "cascade"
                    cascade_delete[back_reference_name] = db_meeting[
                        back_reference_name
                    ]
            references = self.get_references(
                model=self.model,
                id=meeting["id"],
                obj=meeting,
                field_names=["committee_id"],
                deletion_possible=True,
            )
            data.append(
                {
                    "meeting": meeting,
                    "references": references,
                    "cascade_delete": cascade_delete,
                }
            )
        return {"position": self.position, "data": data}

    def create_instance_write_request_element(
        self, position: int, element: Any
    ) -> WriteRequestElement:
        fqid = FullQualifiedId(self.model.collection, element["meeting"]["id"])
        information = {fqid: ["Meeting deleted"]}
        event = Event(type="delete", fqid=fqid)
        return WriteRequestElement(
            events=[event],
            information=information,
            user_id=self.user_id,
            locked_fields={
                FullQualifiedField(self.model.collection, fqid.id, "deleted"): position
            },
        )
