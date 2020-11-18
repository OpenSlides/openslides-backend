from typing import Any, Dict

from ...models.models import PersonalNote
from ...shared.exceptions import ActionException
from ...shared.patterns import FullQualifiedId
from ..default_schema import DefaultSchema
from ..generics import DeleteAction
from ..register import register_action


@register_action("personal_note.delete")
class PersonalNoteDeleteAction(DeleteAction):
    """
    Action to delete a personal note.
    """

    model = PersonalNote()
    schema = DefaultSchema(PersonalNote()).get_delete_schema()

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare item user_id to self.user_id
        """
        personal_note = self.datastore.get(
            FullQualifiedId(self.model.collection, instance["id"]),
            ["user_id"],
        )
        if self.user_id != personal_note.get("user_id"):
            raise ActionException("Cannot delete not owned personal note.")
        return instance
