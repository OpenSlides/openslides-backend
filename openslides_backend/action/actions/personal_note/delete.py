from typing import Any, Dict

from ....models.models import PersonalNote
from ....shared.exceptions import ActionException
from ....shared.patterns import FullQualifiedId
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .mixins import PermissionMixin


@register_action("personal_note.delete")
class PersonalNoteDeleteAction(DeleteAction, PermissionMixin):
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

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        meeting_id = self.get_meeting_id(instance)
        self.check_anonymous_and_user_in_meeting(meeting_id)
