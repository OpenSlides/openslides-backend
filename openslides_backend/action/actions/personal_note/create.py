from typing import Any, Dict

from ....models.models import PersonalNote
from ....shared.exceptions import ActionException
from ....shared.filters import And, FilterOperator
from ...generics.create import CreateAction
from ...mixins.create_action_with_inferred_meeting import (
    CreateActionWithInferredMeetingMixin,
)
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ..meeting_user.create import MeetingUserCreate
from .mixins import PermissionMixin


@register_action("personal_note.create")
class PersonalNoteCreateAction(
    CreateActionWithInferredMeetingMixin, CreateAction, PermissionMixin
):
    """
    Action to create a personal note.
    """

    model = PersonalNote()
    schema = DefaultSchema(PersonalNote()).get_create_schema(
        required_properties=["content_object_id"],
        optional_properties=["star", "note"],
    )
    relation_field_for_meeting = "content_object_id"

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        - set meeting_user_id from action.
        - check star or note.
        - check uniqueness
        """
        filter_ = And(
            FilterOperator("user_id", "=", self.user_id),
            FilterOperator("meeting_id", "=", instance["meeting_id"]),
        )
        filtered_meeting_user = self.datastore.filter(
            "meeting_user", filter_, ["id", "personal_note_ids"]
        )
        if filtered_meeting_user:
            meeting_user = list(filtered_meeting_user.values())[0]
            instance["meeting_user_id"] = meeting_user["id"]
        else:
            action_results = self.execute_other_action(
                MeetingUserCreate,
                [
                    {
                        "user_id": self.user_id,
                        "meeting_id": instance["meeting_id"],
                    }
                ],
            )
            instance["meeting_user_id"] = action_results[0]["id"]  # type: ignore

        if not (instance.get("star") or instance.get("note")):
            raise ActionException("Can't create personal note without star or note.")

        # check, if (meeting_user_id, content_object_id) already in the database.
        filter_ = And(
            FilterOperator("meeting_user_id", "=", instance["meeting_user_id"]),
            FilterOperator(
                "content_object_id", "=", str(instance["content_object_id"])
            ),
        )
        exists = self.datastore.exists(collection=self.model.collection, filter=filter_)
        if exists:
            raise ActionException(
                "(meeting_user_id, content_object_id) must be unique."
            )
        return instance

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        instance = self.update_instance_with_meeting_id(instance)
        self.check_anonymous_and_user_in_meeting(instance["meeting_id"])
