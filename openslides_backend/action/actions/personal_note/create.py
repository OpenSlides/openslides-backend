from typing import Any, Dict

from ....models.models import PersonalNote
from ....shared.exceptions import ActionException
from ....shared.filters import And, FilterOperator
from ...action import PERMISSION_SPECIAL_CASE
from ...generics.create import CreateAction
from ...mixins.create_action_with_inferred_meeting import (
    CreateActionWithInferredMeetingMixin,
)
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("personal_note.create")
class PersonalNoteCreateAction(CreateActionWithInferredMeetingMixin, CreateAction):
    """
    Action to create a personal note.
    """

    model = PersonalNote()
    schema = DefaultSchema(PersonalNote()).get_create_schema(
        required_properties=["content_object_id"],
        optional_properties=["star", "note"],
    )
    permission_description = PERMISSION_SPECIAL_CASE
    relation_field_for_meeting = "content_object_id"

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        * Check user_id if anonymous
        * set user_id from action.
        * check star or note.
        * set meeting_id from content_object_id
        """
        if self.auth.is_anonymous(self.user_id):
            raise ActionException("Can't create personal note for anonymous")
        instance["user_id"] = self.user_id
        if not (instance.get("star") or instance.get("note")):
            raise ActionException("Can't create personal note without star or note.")
        instance = self.update_instance_with_meeting_id(instance)

        # check, if (user_id, content_object_id) already in the databse.
        filter_ = And(
            FilterOperator("user_id", "=", instance["user_id"]),
            FilterOperator(
                "content_object_id", "=", str(instance["content_object_id"])
            ),
        )
        another_exist = self.datastore.exists(
            collection=self.model.collection, filter=filter_
        )
        if another_exist["exists"]:
            raise ActionException("(user_id, content_object_id) must be unique.")
        return instance
