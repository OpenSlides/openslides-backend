from typing import Any, Dict

from ....models.models import Meeting
from ....shared.patterns import fqid_from_collection_and_id
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ..meeting_user.delete import MeetingUserDelete
from ..user.update import UserUpdate
from .mixins import MeetingPermissionMixin


@register_action("meeting.delete")
class MeetingDelete(DeleteAction, MeetingPermissionMixin):
    """
    Action to delete meetings.
    """

    model = Meeting()
    schema = DefaultSchema(Meeting()).get_delete_schema()
    skip_archived_meeting_check = True

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        meeting = self.datastore.get(
            fqid_from_collection_and_id(self.model.collection, instance["id"]),
            ["user_ids", "meeting_user_ids"],
        )
        action_data = [
            {
                "id": user_id,
                **{
                    field: {str(instance["id"]): None}
                    for field in (
                        "number_$",
                        "structure_level_$",
                        "about_me_$",
                        "vote_weight_$",
                    )
                },
            }
            for user_id in meeting.get("user_ids", [])
        ]
        self.execute_other_action(UserUpdate, action_data)
        action_data = [
            {"id": user_meeting_id}
            for user_meeting_id in meeting.get("meeting_user_ids", [])
        ]
        self.execute_other_action(MeetingUserDelete, action_data)

        return instance

    def get_committee_id(self, instance: Dict[str, Any]) -> int:
        meeting = self.datastore.get(
            fqid_from_collection_and_id(self.model.collection, instance["id"]),
            ["committee_id"],
        )
        return meeting["committee_id"]
