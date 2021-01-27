from collections import defaultdict
from typing import Any, Dict, Iterable, List, Union

from ...models.fields import BaseTemplateField
from ...shared.interfaces.event import EventType
from ...shared.interfaces.write_request import WriteRequest
from ...shared.patterns import FullQualifiedId
from ..action import Action
from ..util.typing import ActionResponseResultsElement


class CreateAction(Action):
    """
    Generic create action.
    """

    def base_update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        # Primary instance manipulation for defaults and extra fields.
        instance = self.set_defaults(instance)
        instance = self.validate_fields(instance)

        # Fetch new id to have it available in update_instance method
        new_id = self.datastore.reserve_id(collection=self.model.collection)
        instance["id"] = new_id

        instance = self.update_instance(instance)
        instance = self.validate_relation_fields(instance)

        # Check structured relations and template fields.
        # TODO: this should be unified with the UpdateAction and moved to the relation handling.
        additional_instance_fields: Dict[str, List[str]] = defaultdict(list)
        for field_name in instance:
            if self.model.has_field(field_name):
                field = self.model.get_field(field_name)
                if isinstance(field, BaseTemplateField):
                    structured_fields = self.get_structured_fields_in_instance(
                        field, instance
                    )
                    for instance_field, replacement in structured_fields:
                        template_field_name = (
                            field.own_field_name[: field.index]
                            + "$"
                            + field.own_field_name[field.index :]
                        )
                        additional_instance_fields[template_field_name].append(
                            replacement
                        )
        instance.update(additional_instance_fields)
        return instance

    def set_defaults(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        for field in self.model.get_fields():
            if (
                field.own_field_name not in instance.keys()
                and field.default is not None
            ):
                instance[field.own_field_name] = field.default
        return instance

    def create_write_requests(
        self, instance: Dict[str, Any]
    ) -> Iterable[Union[WriteRequest, ActionResponseResultsElement]]:
        """
        Creates a write request element for one instance of the current model.

        Just prepares a write request element with create event for the given
        instance.
        """
        fqid = FullQualifiedId(self.model.collection, instance["id"])
        information = "Object created"
        yield self.build_write_request(EventType.Create, fqid, information, instance)

        response_info: ActionResponseResultsElement = {"id": fqid.id}
        yield response_info
