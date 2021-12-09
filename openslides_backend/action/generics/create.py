from typing import Any, Dict, Iterable, Optional

from ...shared.interfaces.event import EventType
from ...shared.interfaces.write_request import WriteRequest
from ...shared.patterns import FullQualifiedId
from ..action import Action
from ..util.typing import ActionData, ActionResultElement


class CreateAction(Action):
    """
    Generic create action.
    """

    def pre_get_ids(self, action_data: ActionData) -> ActionData:
        if not action_data:
            return action_data
        new_ids = self.datastore.reserve_ids(
            collection=self.model.collection, amount=len(list(action_data))
        )
        for instance, new_id in zip(action_data, new_ids):
            instance["id"] = new_id
        return action_data

    def base_update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        # Primary instance manipulation for defaults and extra fields.
        instance = self.set_defaults(instance)
        instance = self.validate_fields(instance)

        instance = self.update_instance(instance)
        self.apply_instance(instance)
        self.validate_relation_fields(instance)

        return instance

    def set_defaults(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        for field in self.model.get_fields():
            if (
                field.own_field_name not in instance.keys()
                and field.default is not None
            ):
                instance[field.own_field_name] = field.default
        return instance

    def create_write_requests(self, instance: Dict[str, Any]) -> Iterable[WriteRequest]:
        """
        Creates a write request element for one instance of the current model.
        Just prepares a write request element with create event for the given
        instance.
        """
        fqid = FullQualifiedId(self.model.collection, instance["id"])
        information = "Object created"
        yield self.build_write_request(EventType.Create, fqid, information, instance)

    def create_action_result_element(
        self, instance: Dict[str, Any]
    ) -> Optional[ActionResultElement]:
        """Returns the newly created id."""
        return {"id": instance["id"]}
