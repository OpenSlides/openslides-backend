from ....action.util.typing import ActionData, ActionResults
from ....models.models import Organization
from ....permissions.management_levels import OrganizationManagementLevel
from ...ddaction import DDAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ..history_position.delete import HistoryPositionDelete


@register_action("organization.delete_history_information")
class DeleteHistoryInformation(DDAction):
    """
    Action to delete history information.
    """

    model = Organization()
    schema = DefaultSchema(Organization()).get_update_schema()
    skip_archived_meeting_check = True
    permission = OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION

    def write_instances(self, action_data: ActionData) -> ActionResults | None:
        all_positions = self.database.get_all("history_position", ["id"])
        self.execute_other_action(
            HistoryPositionDelete, [{"id": id_} for id_ in all_positions]
        )
        return list(action_data)
