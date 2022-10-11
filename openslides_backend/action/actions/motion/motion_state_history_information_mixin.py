from typing import List, Optional

from openslides_backend.shared.patterns import fqid_from_collection_and_id

from ...action import Action


class MotionStateHistoryInformationMixin(Action):
    def _get_state_history_information(
        self, instance_field: str, name_field: str, verbose_model: str
    ) -> Optional[List[str]]:
        all_ids = set(instance[instance_field] for instance in self.instances)
        if len(all_ids) == 1:
            single_id = all_ids.pop()
            instance = self.datastore.get(
                fqid_from_collection_and_id("motion_state", single_id),
                [name_field],
                lock_result=False,
            )
            return [verbose_model + " set to {}", instance[name_field]]
        else:
            return [verbose_model + " changed"]
