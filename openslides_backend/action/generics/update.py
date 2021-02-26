from typing import Any, Dict, Iterable

from ...shared.interfaces.event import EventType
from ...shared.interfaces.write_request import WriteRequest
from ...shared.patterns import FullQualifiedId
from ..action import Action


class UpdateAction(Action):
    """
    Generic update action.
    """

    def base_update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        # Primary instance manipulation for defaults and extra fields.
        instance = self.validate_fields(instance)
        self.datastore.additional_relation_models[
            FullQualifiedId(self.model.collection, instance["id"])
        ] = instance

        instance = self.update_instance(instance)
        instance = self.validate_relation_fields(instance)

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
        updated_instance = super().validate_relation_fields({**instance, **db_instance})
        for field_name in missing_fields:
            if field_name in updated_instance:
                del updated_instance[field_name]
        return updated_instance

    def create_write_requests(self, instance: Dict[str, Any]) -> Iterable[WriteRequest]:
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
        yield self.build_write_request(EventType.Update, fqid, information, fields)
