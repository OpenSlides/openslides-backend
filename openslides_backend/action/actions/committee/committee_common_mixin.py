from typing import Any, Dict

from ....shared.exceptions import ActionException
from ...action import Action


class CommitteeCommonCreateUpdateMixin(Action):
    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        instance = super().update_instance(instance)
        id = instance.get("id")
        if id in instance.get("forward_to_committee_ids", []) or id in instance.get(
            "receive_forwardings_from_committee_ids", []
        ):
            raise ActionException(
                "Forwarding or receiving from own committee is not possible!"
            )
        return instance
