from typing import Any, Dict, Set

from ....action.mixins.archived_meeting_check_mixin import CheckForArchivedMeetingMixin
from ....permissions.management_levels import CommitteeManagementLevel
from ....services.datastore.commands import GetManyRequest
from ....shared.exceptions import ActionException
from ....shared.patterns import Collection
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
        old_manager_ids: Set[int] = None,
        old_user_ids: Set[int] = None,
    ) -> None:
        if old_manager_ids is None:
            old_manager_ids = set()
        if old_user_ids is None:
            old_user_ids = set()
        action_data = []
        remove_manager_ids = set()
        if "manager_ids" in instance:
            new_manager_ids = set(instance.pop("manager_ids"))
            to_add = new_manager_ids - old_manager_ids
            remove_manager_ids = old_manager_ids - new_manager_ids
            if "user_ids" in instance:
                instance["user_ids"] = list(set(instance["user_ids"]) | new_manager_ids)

            if to_add:
                get_many_request = GetManyRequest(
                    Collection("user"),
                    list(to_add),
                    ["committee_ids"],
                )
                gm_result = self.datastore.get_many([get_many_request])
                managers = gm_result.get(Collection("user"), {})
            for manager_id in to_add:
                manager = managers.get(manager_id, {})
                committee_ids = manager.get("committee_ids", [])
                if instance["id"] not in committee_ids:
                    committee_ids.append(instance["id"])
                action_data.append(
                    {
                        "id": manager_id,
                        "committee_$_management_level": {
                            str(instance["id"]): CommitteeManagementLevel.CAN_MANAGE,
                        },
                        "committee_ids": committee_ids,
                    }
                )

        if "user_ids" in instance:
            remove_manager_ids = remove_manager_ids | (
                (old_user_ids - set(instance["user_ids"])) & old_manager_ids
            )
        for manager_id in remove_manager_ids:
            action_data.append(
                {
                    "id": manager_id,
                    "committee_$_management_level": {str(instance["id"]): None},
                }
            )
        if action_data:
            self.execute_other_action(UserUpdate, action_data)
