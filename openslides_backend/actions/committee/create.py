import fastjsonschema  # type: ignore

from ...models.committee import Committee
from ...shared.permissions.committee import COMMITTEE_CAN_MANAGE
from ...shared.schema import schema_version
from ..actions import register_action
from ..generics import CreateAction

create_committee_schema = fastjsonschema.compile(
    {
        "$schema": schema_version,
        "title": "New committees schema",
        "description": "An array of new committees.",
        "type": "array",
        "items": {
            "type": "object",
            "properties": Committee().get_properties("organisation_id", "title"),
            "required": ["organisation_id", "title"],
            "additionalProperties": False,
        },
        "minItems": 1,
        "uniqueItems": True,
    }
)


@register_action("committee.create")
class CommitteeCreate(CreateAction):
    """
    Action to create committees.
    """

    model = Committee()
    schema = create_committee_schema
    permission_reference = "organisation_id"
    permissions = [COMMITTEE_CAN_MANAGE]
