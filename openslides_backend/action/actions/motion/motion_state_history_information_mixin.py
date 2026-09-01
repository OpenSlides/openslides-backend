from openslides_backend.shared.patterns import fqid_from_collection_and_id
from openslides_backend.shared.typing import HistoryInformation

from ...action import Action


class MotionStateHistoryInformationMixin(Action):
    def _get_state_history_information(
        self, instance_field: str, verbose_model: str
    ) -> HistoryInformation:
        return {
            fqid_from_collection_and_id(self.model.collection, instance["id"]): [
                verbose_model + " set to {}",
                fqid_from_collection_and_id("motion_state", instance[instance_field]),
            ]
            for instance in self.instances
        }
