from typing import Any, Dict, Set

from ....permissions.management_levels import CommitteeManagementLevel
from ....services.datastore.commands import GetManyRequest
from ....shared.exceptions import ActionException
from ....shared.patterns import Collection
from ...action import Action
from ..user.update import UserUpdate


class CommitteeCommonCreateUpdateMixin(Action):
    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """Check if own committee is forwarded or received explicitly,
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
        committee_id: int,
        new_manager_ids: Set[int],
        old_manager_ids: Set[int],
        create_case: bool,
    ) -> None:
        action_data = []
        if new_manager_ids - old_manager_ids and create_case:
            get_many_request = GetManyRequest(
                Collection("user"),
                list(new_manager_ids - old_manager_ids),
                ["committee_ids"],
            )
            gm_result = self.datastore.get_many([get_many_request])
            managers = gm_result.get(Collection("user"), {})
        for manager_id in new_manager_ids - old_manager_ids:
            data = {
                "id": manager_id,
                "committee_$_management_level": {
                    str(committee_id): CommitteeManagementLevel.CAN_MANAGE,
                },
            }
            if create_case:
                manager = managers.get(manager_id, {})
                data["committee_ids"] = manager.get("committee_ids", []) + [
                    committee_id
                ]
            action_data.append(data)
        for manager_id in old_manager_ids - new_manager_ids:
            action_data.append(
                {
                    "id": manager_id,
                    "committee_$_management_level": {str(committee_id): None},
                }
            )
        if action_data:
            self.execute_other_action(UserUpdate, action_data)
