from collections.abc import Iterable
from typing import Any

from ...shared.interfaces.event import Event, EventType
from ...shared.patterns import fqid_from_collection_and_id
from ..action import Action
from ..util.typing import ActionData, ActionResultElement


class CreateAction(Action):
    """
    Generic create action.
    """

    def prepare_action_data(self, action_data: ActionData) -> ActionData:
        if not action_data:
            return action_data
        new_ids = self.datastore.reserve_ids(
            collection=self.model.collection, amount=len(list(action_data))
        )
        for instance, new_id in zip(action_data, new_ids):
            instance["id"] = new_id
        return action_data

    def base_update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        # Primary instance manipulation for defaults and extra fields.
        instance = self.set_defaults(instance)

        instance["meta_new"] = True  # mark as a new model
        instance = self.update_instance(instance)
        self.apply_instance(instance)
        self.validate_relation_fields(instance)

        return instance

    def set_defaults(self, instance: dict[str, Any]) -> dict[str, Any]:
        for field in self.model.get_fields():
            if (
                field.own_field_name not in instance.keys()
                and field.default is not None
            ):
                instance[field.own_field_name] = field.default
        return instance

    def create_events(self, instance: dict[str, Any]) -> Iterable[Event]:
        """
        Creates events for one instance of the current model.
        """
        fqid = fqid_from_collection_and_id(self.model.collection, instance["id"])
        if "meta_new" in instance:
            del instance["meta_new"]
        yield self.build_event(EventType.Create, fqid, instance)

    def create_action_result_element(
        self, instance: dict[str, Any]
    ) -> ActionResultElement | None:
        """Returns the newly created id."""
        return {"id": instance["id"]}
