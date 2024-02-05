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

    def get_committee_id(self, instance: dict[str, Any]) -> int:
        meeting = self.datastore.get(
            fqid_from_collection_and_id(self.model.collection, instance["id"]),
            ["committee_id"],
        )
        return meeting["committee_id"]
