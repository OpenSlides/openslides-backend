from typing import Any, Dict, Iterable

from ...shared.interfaces.event import EventType
from ...shared.interfaces.write_request import WriteRequest
from ...shared.patterns import to_fqid
from ..action import Action


class UpdateAction(Action):
    """
    Generic update action.
    """

    def base_update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        # Primary instance manipulation for defaults and extra fields.
        instance = self.validate_fields(instance)
        instance = self.update_instance(instance)
        self.apply_instance(instance)

        self.validate_relation_fields(instance)

        return instance

    def create_write_requests(self, instance: Dict[str, Any]) -> Iterable[WriteRequest]:
        """
        Creates a write request element for one instance of the current model.
        Just prepares a write request element with update event for the given
        instance.
        """
        fqid = to_fqid(self.model.collection, instance["id"])
        information = "Object updated"
        fields = {
            k: v for k, v in instance.items() if k != "id" and not k.startswith("meta_")
        }
        if not fields:
            return []
        yield self.build_write_request(EventType.Update, fqid, information, fields)
