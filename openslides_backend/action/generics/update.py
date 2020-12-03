from collections import defaultdict
from typing import Any, Dict, Iterable, Set, Union

from ...models.fields import BaseTemplateField
from ...shared.interfaces.event import EventType
from ...shared.interfaces.write_request_element import WriteRequestElement
from ...shared.patterns import FullQualifiedId
from ..action import Action
from ..util.typing import ActionResponseResultsElement


class UpdateAction(Action):
    """
    Generic update action.
    """

    def base_update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        # TODO: Check if instance exists in DB and is not deleted. Ensure that object or meta_deleted field is added to locked_fields.

        # Primary instance manipulation for defaults and extra fields.
        instance = self.validate_fields(instance)
        instance = self.update_instance(instance)
        instance = self.validate_relation_fields(instance)

        if not isinstance(instance.get("id"), int):
            raise TypeError(f"Instance {instance} of payload must contain integer id.")

        # Check structured relations and template fields.
        # TODO: this should be unified with the CreateAction and moved to the relation handling.
        additional_instance_fields: Dict[str, Set[str]] = defaultdict(set)
        for field_name in instance:
            if self.model.has_field(field_name):
                field = self.model.get_field(field_name)
                if isinstance(field, BaseTemplateField):
                    template_field_name = (
                        field.own_field_name[: field.index]
                        + "$"
                        + field.own_field_name[field.index :]
                    )
                    template_field_db_value = set(
                        self.fetch_model(
                            fqid=FullQualifiedId(self.model.collection, instance["id"]),
                            mapped_fields=[template_field_name],
                        ).get(template_field_name, [])
                    )
                    replacement = field.get_replacement(field_name)
                    if instance[field_name]:
                        if replacement not in template_field_db_value:
                            additional_instance_fields[template_field_name].update(
                                template_field_db_value, set([replacement])
                            )
                    else:
                        if replacement in template_field_db_value:
                            additional_instance_fields[template_field_name].update(
                                template_field_db_value
                            )
                            additional_instance_fields[template_field_name].remove(
                                replacement
                            )
        for k, v in additional_instance_fields.items():
            # instance.update(...) but with type changing from set to list
            instance[k] = list(v)

        return instance

    def validate_relation_fields(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetches missing fields from db for field equality check and removes them after.
        """
        missing_fields = [
            equal_field_name
            for field in self.model.get_relation_fields()
            if field.equal_fields and field.own_field_name in instance
            for equal_field_name in field.equal_fields
            if equal_field_name not in instance
        ]
        if missing_fields:
            db_instance = self.fetch_model(
                FullQualifiedId(self.model.collection, instance["id"]), missing_fields
            )
        else:
            db_instance = {}
        updated_instance = super().validate_fields({**instance, **db_instance})
        for field_name in missing_fields:
            if field_name in updated_instance:
                del updated_instance[field_name]
        return updated_instance

    def create_write_request_elements(
        self, instance: Dict[str, Any]
    ) -> Iterable[Union[WriteRequestElement, ActionResponseResultsElement]]:
        """
        Creates a write request element for one instance of the current model.

        Just prepares a write request element with update event for the given
        instance.
        """
        fqid = FullQualifiedId(self.model.collection, instance["id"])
        information = "Object updated"
        fields = {
            k: v for k, v in instance.items() if k != "id" and not k.startswith("meta_")
        }
        yield self.build_write_request_element(
            EventType.Update, fqid, information, fields
        )
