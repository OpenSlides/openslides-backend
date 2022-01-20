from typing import Any, Dict

from ....action.mixins.archived_meeting_check_mixin import CheckForArchivedMeetingMixin
from ....shared.exceptions import ActionException


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
