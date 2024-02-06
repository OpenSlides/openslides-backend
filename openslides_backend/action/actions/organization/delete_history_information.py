from collections.abc import Iterable
from typing import Any

from ....models.models import Organization
from ....permissions.management_levels import OrganizationManagementLevel
from ...action import Action, Event
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("organization.delete_history_information")
class DeleteHistoryInformation(Action):
    """
    Action to delete history information.
    """

    model = Organization()
    schema = DefaultSchema(Organization()).get_update_schema()
    skip_archived_meeting_check = True
    permission = OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        self.datastore.delete_history_information()
        return instance

    def create_events(self, instance: dict[str, Any]) -> Iterable[Event]:
        return []
