from typing import Any, Dict, Set

from ....action.mixins.archived_meeting_check_mixin import CheckForArchivedMeetingMixin
from ....permissions.management_levels import CommitteeManagementLevel
from ....shared.exceptions import ActionException
from ..user.update import UserUpdate


class CommitteeCommonCreateUpdateMixin(CheckForArchivedMeetingMixin):
    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if own committee is forwarded or received explicitly,
        it may not be excluded by the opposite setting
        """
        instance = super().update_instance(instance)
        if (
            instance.get("forward_to_committee_ids") is None
            or instance.get("receive_forwardings_from_committee_ids") is None
        ):
            return instance
        id = instance.get("id")
        if (id in instance.get("forward_to_committee_ids", [])) != (
            id in instance.get("receive_forwardings_from_committee_ids", [])
        ):
            raise ActionException(
                "Forwarding or receiving to/from own must be configured in both directions!"
            )
        return instance

    def update_managers(
        self,
        instance: Dict[str, Any],
        committee_manager_ids: Set[int] = None,
    ) -> None:
        if committee_manager_ids is None:
            committee_manager_ids = set()
        action_data = []
        new_manager_ids = set(instance.pop("manager_ids"))
        managers_to_add = new_manager_ids - committee_manager_ids
        managers_to_remove = committee_manager_ids - new_manager_ids

        for manager_id in managers_to_add:
            action_data.append(
                {
                    "id": manager_id,
                    "committee_$_management_level": {
                        str(instance["id"]): CommitteeManagementLevel.CAN_MANAGE,
                    },
                }
            )

        for manager_id in managers_to_remove:
            action_data.append(
                {
                    "id": manager_id,
                    "committee_$_management_level": {str(instance["id"]): None},
                }
            )
        if action_data:
            self.execute_other_action(UserUpdate, action_data)
