from typing import Any, Dict

from ....models.models import PersonalNote
from ....shared.exceptions import ActionException
from ....shared.patterns import FullQualifiedId
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("personal_note.update")
class PersonalNoteUpdateAction(UpdateAction):
    """
    Action to update a personal note.
    """

    model = PersonalNote()
    schema = DefaultSchema(PersonalNote()).get_update_schema(
        optional_properties=["star", "note"]
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare item user_id to self.user_id
        """
        personal_note = self.datastore.get(
            FullQualifiedId(self.model.collection, instance["id"]),
            ["user_id"],
        )
        if self.user_id != personal_note.get("user_id"):
            raise ActionException("Cannot change not owned personal note.")
        return instance
