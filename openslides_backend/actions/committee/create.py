from typing import Any

import fastjsonschema  # type: ignore

from ...models.committee import Committee
from ...shared.exceptions import PermissionDenied
from ...shared.interfaces import Event, WriteRequestElement
from ...shared.patterns import FullQualifiedField, FullQualifiedId
from ...shared.permissions.committee import COMMITTEE_CAN_MANAGE
from ...shared.schema import schema_version
from ..actions import register_action
from ..actions_interface import Payload
from ..base import Action, DataSet

create_committee_schema = fastjsonschema.compile(
    {
        "$schema": schema_version,
        "title": "New committees schema",
        "description": "An array of new committees.",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "organisation_id": Committee().get_schema("organisation_id"),
                "title": Committee().get_schema("title"),
            },
            "required": ["organisation_id", "title"],
        },
        "minItems": 1,
        "uniqueItems": True,
    }
)


@register_action("committee.create")
class CommitteeCreate(Action):
    """
    Action to create committees.
    """

    model = Committee()
    schema = create_committee_schema

    def check_permission(self, organisation_id: int) -> None:
        required_permission = f"{organisation_id}/{COMMITTEE_CAN_MANAGE}"
        if not self.permission.has_perm(self.user_id, required_permission):
            raise PermissionDenied(
                f"User does not have {COMMITTEE_CAN_MANAGE} permission for organisation {organisation_id}."
            )

    def prepare_dataset(self, payload: Payload) -> DataSet:
        data = []
        for committee in payload:
            self.check_permission(committee["organisation_id"])
            id, position = self.database.getId(collection=self.model.collection)
            self.set_min_position(position)
            references = self.get_references(
                model=self.model, id=id, obj=committee, fields=["organisation_id"],
            )
            data.append(
                {"committee": committee, "new_id": id, "references": references}
            )
        return {"position": self.position, "data": data}

    def create_instance_write_request_element(
        self, position: int, element: Any
    ) -> WriteRequestElement:
        fqfields = {}

        # Organisation
        fqfields[
            FullQualifiedField(
                self.model.collection, element["new_id"], "organisation_id"
            )
        ] = element["committee"]["organisation_id"]

        # Title
        fqfields[
            FullQualifiedField(self.model.collection, element["new_id"], "title")
        ] = element["committee"]["title"]

        information = {
            FullQualifiedId(self.model.collection, element["new_id"]): [
                "Committee created"
            ]
        }
        event = Event(type="create", fqfields=fqfields)
        return WriteRequestElement(
            events=[event],
            information=information,
            user_id=self.user_id,
            locked_fields={},
        )
