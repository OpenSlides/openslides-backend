from typing import Any

from ....models.models import PersonalNote
from ....shared.exceptions import ActionException
from ....shared.filters import And, FilterOperator
from ...generics.create import CreateAction
from ...mixins.create_action_with_inferred_meeting import (
    CreateActionWithInferredMeetingMixin,
)
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .mixins import PermissionMixin


@register_action("personal_note.create")
class PersonalNoteCreateAction(
    CreateActionWithInferredMeetingMixin, CreateAction, PermissionMixin
):
    """
    Action to create a personal note.
    """

    internal_id_fields = [
        "meeting_user_id",
    ]

    model = PersonalNote()
    schema = DefaultSchema(PersonalNote()).get_create_schema(
        required_properties=["content_object_id"],
        optional_properties=["star", "note", *internal_id_fields],
    )
    relation_field_for_meeting = "content_object_id"

    def validate_instance(self, instance: dict[str, Any]) -> None:
        super().validate_instance(instance)
        if not self.internal and any(
            forbidden_keys_used := {
                key for key in instance if key in self.internal_id_fields
            }
        ):
            raise ActionException(
                f"data must not contain {forbidden_keys_used} properties"
            )

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        """
        - set meeting_user_id from action.
        - check star or note.
        - check uniqueness
        """
        if "meeting_id" not in instance:
            instance = self.update_instance_with_meeting_id(instance)
        if "meeting_user_id" not in instance:
            filter_ = And(
                FilterOperator("user_id", "=", self.user_id),
                FilterOperator("meeting_id", "=", instance["meeting_id"]),
            )
            filtered_meeting_user = self.datastore.filter(
                "meeting_user", filter_, ["id", "personal_note_ids"]
            )
            meeting_user = list(filtered_meeting_user.values())[0]
            instance["meeting_user_id"] = meeting_user["id"]

        if not (instance.get("star") or instance.get("note")):
            raise ActionException("Can't create personal note without star or note.")

        # check, if (meeting_user_id, content_object_id) already in the database.
        filter_ = And(
            FilterOperator("meeting_user_id", "=", instance["meeting_user_id"]),
            FilterOperator(
                "content_object_id", "=", str(instance["content_object_id"])
            ),
        )
        exists = self.datastore.exists(
            collection=self.model.collection, filter_=filter_
        )
        if exists:
            raise ActionException(
                "(meeting_user_id, content_object_id) must be unique."
            )
        return instance

    def check_permissions(self, instance: dict[str, Any]) -> None:
        instance = self.update_instance_with_meeting_id(instance)
        self.check_anonymous_and_user_in_meeting(instance["meeting_id"])
