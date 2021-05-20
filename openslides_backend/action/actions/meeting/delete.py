from typing import Any, Dict

from ....models.models import Meeting
from ....shared.patterns import FullQualifiedId
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

    def get_committee_id(self, instance: Dict[str, Any]) -> int:
        meeting = self.datastore.get(
            FullQualifiedId(self.model.collection, instance["id"]), ["committee_id"]
        )
        return meeting["committee_id"]
