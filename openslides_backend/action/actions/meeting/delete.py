from typing import Any

from ....models.models import Meeting
from ....shared.patterns import fqid_from_collection_and_id
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .mixins import MeetingPermissionMixin


@register_action("meeting.delete")
class MeetingDelete(DeleteAction, MeetingPermissionMixin):
    """
    Action to delete meetings.
    """

    model = Meeting()
    schema = DefaultSchema(Meeting()).get_delete_schema()
    skip_archived_meeting_check = True
    action_name = "delete"

    def get_committee_id(self, instance: dict[str, Any]) -> int:
        meeting = self.datastore.get(
            fqid_from_collection_and_id(self.model.collection, instance["id"]),
            ["committee_id"],
        )
        return meeting["committee_id"]

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        """
        Handle deletion of polls and all the related instances in the vote service.
        """
        poll_ids = self.datastore.get(f"meeting/{instance['id']}", ["poll_ids"]).get(
            "poll_ids", []
        )
        for poll_id in poll_ids:
            self.vote_service.delete(poll_id)
            self.datastore.apply_to_be_deleted(f"poll/{poll_id}")
        return instance
