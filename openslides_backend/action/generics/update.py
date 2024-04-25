from collections.abc import Iterable
from typing import Any

from ...shared.interfaces.event import Event, EventType
from ...shared.patterns import fqid_from_collection_and_id
from ..action import Action


class UpdateAction(Action):
    """
    Generic update action.
    """

    def base_update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        # Primary instance manipulation for defaults and extra fields.
        instance = self.update_instance(instance)
        self.apply_instance(instance)

        self.validate_relation_fields(instance)

        return instance

    def create_events(self, instance: dict[str, Any]) -> Iterable[Event]:
        """
        Creates events for one instance of the current model.
        """
        fqid = fqid_from_collection_and_id(self.model.collection, instance["id"])
        fields = {
            k: v for k, v in instance.items() if k != "id" and not k.startswith("meta_")
        }
        if not fields:
            return []  # type: ignore # since mypy 1.10.0 appears: error: No return value expected  [return-value]
        yield self.build_event(EventType.Update, fqid, fields)
