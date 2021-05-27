from typing import Any, Dict

from ...models.fields import Field
from ...shared.patterns import Collection, FullQualifiedField
from .calculated_field_handler import CalculatedFieldHandler
from .typing import FieldUpdateElement, RelationUpdates


class UserMeetingIdsHandler(CalculatedFieldHandler):
    """
    CalculatedFieldHandler to fill the user.meeting_ids.
    """

    def process_field(
        self, field: Field, field_name: str, instance: Dict[str, Any], action: str
    ) -> RelationUpdates:
        if field_name != "group_$_ids":
            return {}
        value = set(int(x) for x in instance.get(field_name, []))
        relation_el: FieldUpdateElement = {  # type: ignore
            "type": "add",
            "value": list(value),
        }
        fqfield = FullQualifiedField(Collection("user"), instance["id"], "meeting_ids")
        return {fqfield: relation_el}
