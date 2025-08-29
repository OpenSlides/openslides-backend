from typing import Any

from openslides_backend.action.actions.topic.delete import TopicDelete

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

    def update_instance(self, instance: dict[str, Any]) -> dict:
        meeting = self.datastore.get(
            fqid_from_collection_and_id("meeting", instance["id"]), []
        )
        if topic_ids := meeting.get("topic_ids"):
            for topic_fqid in topic_ids:
                self.execute_other_action(TopicDelete, [{"id": topic_fqid}])
        return instance
