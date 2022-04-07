from typing import Any, Dict, List

from ....services.datastore.interface import GetManyRequest
from ...action import Action


class SetCreatedTimestampMixin(Action):
    def handle_old_set_created_timestamp(
        self, instance: Dict[str, Any], state_ids: List[int], update_class: Any
    ) -> None:

        # handle old set_created_timestamp
        if instance.get("set_created_timestamp") and state_ids:
            gmr = GetManyRequest(
                self.model.collection,
                state_ids,
                ["id", "set_created_timestamp"],
            )
            gm_results = self.datastore.get_many([gmr])
            for state in gm_results.get(self.model.collection, {}).values():
                if state.get("set_created_timestamp") and state["id"] != instance["id"]:
                    self.execute_other_action(
                        update_class,
                        [{"id": state["id"], "set_created_timestamp": False}],
                    )
