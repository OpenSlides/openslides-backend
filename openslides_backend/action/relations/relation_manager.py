from typing import Any, Dict, List, cast

from ...models.base import Model, model_registry
from ...models.fields import BaseRelationField, Field
from ...services.datastore.interface import DatastoreService
from ...shared.patterns import FullQualifiedField
from ...shared.typing import ModelMap
from .calculated_field_handlers_map import calculated_field_handlers_map
from .single_relation_handler import SingleRelationHandler
from .typing import (
    FieldUpdateElement,
    ListUpdateElement,
    RelationUpdateElement,
    RelationUpdates,
)


class RelationManager:
    datastore: DatastoreService

    relation_field_updates: RelationUpdates

    def __init__(self, datastore: DatastoreService) -> None:
        self.datastore = datastore
        self.relation_field_updates = {}

    def get_relation_updates(
        self,
        model: Model,
        instance: Dict[str, Any],
        action: str,
        additional_relation_models: ModelMap = {},
    ) -> RelationUpdates:
        # id has to be provided to be able to correctly update relations
        assert "id" in instance
        relations: RelationUpdates = {}
        for field_name in instance:
            if not model.has_field(field_name):
                continue
            field = model.get_field(field_name)

            # process calculated fields handlers
            self.call_calculated_field_handlers(
                relations, field, field_name, instance, action
            )

            # only relations are handled here
            if not isinstance(field, BaseRelationField):
                continue
            # ignore template fields, we have to do no relation handling there
            if "$_" in field_name or field_name[-1] == "$":
                continue

            handler = SingleRelationHandler(
                self.datastore,
                field,
                field_name,
                instance,
                additional_relation_models=additional_relation_models,
            )
            result = handler.perform()
            for fqfield, relations_element in result.items():
                self.process_relation_element(fqfield, relations_element, relations)

                # call calculated field handlers again on updated related field
                related_field_name = fqfield.field
                related_model = model_registry[fqfield.collection]()
                related_field = related_model.get_field(related_field_name)
                related_instance = {
                    "id": fqfield.id,
                    related_field_name: relations_element["value"],
                }
                self.call_calculated_field_handlers(
                    relations,
                    related_field,
                    related_field_name,
                    related_instance,
                    action,
                )

        return relations

    def call_calculated_field_handlers(
        self,
        relations: RelationUpdates,
        field: Field,
        field_name: str,
        instance: Dict[str, Any],
        action: str,
    ) -> None:
        """
        Calls all registered CalculatedFieldHandlers for the current field and adds the
        resulting relation updates to the main map.
        """
        for calculated_field_handler_class in calculated_field_handlers_map[field]:
            handler_instance = calculated_field_handler_class(self.datastore)
            result = handler_instance.process_field(field, field_name, instance, action)
            for fqfield, relations_element in result.items():
                self.process_relation_element(fqfield, relations_element, relations)

    def process_relation_element(
        self,
        fqfield: FullQualifiedField,
        relation_update_element: RelationUpdateElement,
        relations: RelationUpdates,
    ) -> None:
        """
        Processes the given RelationUpdateElement. If the fqfield is not in relations
        yet, it can just be added, else the old relation update has to be merged with
        the new one.
        """
        relations_element = cast(FieldUpdateElement, relation_update_element)
        if fqfield in self.relation_field_updates and (
            "value" not in relations_element
            or isinstance(relations_element["value"], list)
        ):
            relation_update_element = self.merge_relation_elements(
                self.relation_field_updates[fqfield], relation_update_element
            )
        relations[fqfield] = self.relation_field_updates[
            fqfield
        ] = relation_update_element

    def merge_relation_elements(
        self,
        a: RelationUpdateElement,
        b: RelationUpdateElement,
    ) -> RelationUpdateElement:
        """
        Merges two given RelationUpdateElements. There are 4 cases:
        a = b = FieldUpdateElements
            With the information "add"/"remove" and "modified_element" the new element
            can be calculated. The new "modified_field_element" is no longer correct,
            but since it isn't needed later, it doesn't matter.
        a = FieldUpdateElement, b = ListUpdateElement
            b can just be applied to a.
        a = b = ListUpdateElement
            The two ListUpdateElements can just be combined into one.
        a = ListUpdateElement, b = FieldUpdateElement
            Not possible and currently not needed.
        """
        # list field is updated, merge updates
        if a["type"] in ("add", "remove"):
            a = cast(FieldUpdateElement, a)
            assert isinstance(a["value"], list)
            new_value: List[Any] = a["value"]
            if b["type"] == "add":
                b = cast(FieldUpdateElement, b)
                new_value.append(b["modified_element"])
            elif b["type"] == "remove":
                b = cast(FieldUpdateElement, b)
                new_value = [x for x in new_value if x != b["modified_element"]]
            else:
                b = cast(ListUpdateElement, b)
                new_value = [x for x in new_value if x not in b.get("remove", [])]
                new_value.extend(b.get("add", []))
            a["value"] = new_value
        elif b["type"] == "list_update":
            a = cast(ListUpdateElement, a)
            b = cast(ListUpdateElement, b)
            new_add: List[Any] = a.get("add", [])
            new_remove: List[Any] = a.get("remove", [])
            new_add = [x for x in new_add if x not in b.get("remove", [])]
            new_add += [x for x in b.get("add", []) if x not in new_add]
            new_remove = [x for x in new_remove if x not in new_add]
            new_remove += [x for x in b.get("remove", []) if x not in new_remove]
            a["add"] = new_add
            a["remove"] = new_remove
        else:
            raise NotImplementedError()
        return a
