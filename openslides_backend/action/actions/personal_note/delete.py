from typing import Any

from ....models.models import PersonalNote
from ....shared.exceptions import PermissionDenied
from ....shared.patterns import fqid_from_collection_and_id
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

    def check_permissions(self, instance: dict[str, Any]) -> None:
        meeting_id = self.get_meeting_id(instance)
        self.check_anonymous_and_user_in_meeting(meeting_id)
        personal_note = self.datastore.get(
            fqid_from_collection_and_id(self.model.collection, instance["id"]),
            ["meeting_user_id"],
            lock_result=False,
        )
        user = self.datastore.get(
            fqid_from_collection_and_id("user", self.user_id),
            ["meeting_user_ids"],
            lock_result=False,
        )
        if personal_note.get("meeting_user_id") not in (
            user.get("meeting_user_ids") or []
        ):
            raise PermissionDenied("Cannot delete not owned personal note.")
