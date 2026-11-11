from typing import Any, cast

from ...models.base import Model
from ...models.fields import BaseRelationField
from ...services.database.interface import Database
from ...shared.patterns import FullQualifiedField, field_from_fqfield, fqid_from_fqfield
from .single_relation_handler import SingleRelationHandler
from .typing import (
    FieldUpdateElement,
    ListUpdateElement,
    RelationUpdateElement,
    RelationUpdates,
)


class RelationManager:
    datastore: Database

    relation_field_updates: RelationUpdates

    def __init__(self, datastore: Database) -> None:
        self.datastore = datastore
        self.relation_field_updates = {}

    def get_relation_updates(
        self,
        model: Model,
        instance: dict[str, Any],
        action: str,
    ) -> RelationUpdates:
        # id has to be provided to be able to correctly update relations
        assert "id" in instance

        relations: RelationUpdates = {}
        for field_name in instance:
            if not model.has_field(field_name):
                continue
            field = model.get_field(field_name)

            # only relations are handled here
            if not isinstance(field, BaseRelationField):
                continue

            handler = SingleRelationHandler(
                self.datastore,
                field,
                field_name,
                instance,
            )
            result = handler.perform()
            for fqfield, relations_element in result.items():
                self.process_relation_element(fqfield, relations_element, relations)

        self.apply_relation_updates(relations)
        return relations

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
        relations[fqfield] = self.relation_field_updates[fqfield] = (
            relation_update_element
        )

    def apply_relation_updates(self, relations: RelationUpdates) -> None:
        """
        Applies all given relations updates to the additional models in the datastore.
        """
        for fqfield, relations_element in relations.items():
            if relations_element["type"] in ("add", "remove"):
                field_update_element = cast(FieldUpdateElement, relations_element)
                self.datastore.apply_changed_model(
                    fqid_from_fqfield(fqfield),
                    {field_from_fqfield(fqfield): field_update_element["value"]},
                )
            elif relations_element["type"] == "list_update":
                # list updates are only issued by calculated field handlers and therefore must not be handled here
                raise NotImplementedError("List updates should not occur at this point")
            else:
                raise NotImplementedError("Invalid relations element type")

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
            The FieldUpdate is more specific and therefore overrides the ListUpdate.
        """
        # list field is updated, merge updates
        if a["type"] in ("add", "remove"):
            a = cast(FieldUpdateElement, a)
            assert isinstance(a["value"], list)
            new_value: list[Any] = list(a["value"])  # copy list to prevent data leaks
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
            new_add: list[Any] = a.get("add", [])
            new_remove: list[Any] = a.get("remove", [])
            new_add = [x for x in new_add if x not in b.get("remove", [])]
            new_add += [x for x in b.get("add", []) if x not in new_add]
            new_remove = [x for x in new_remove if x not in new_add]
            new_remove += [x for x in b.get("remove", []) if x not in new_remove]
            a["add"] = new_add
            a["remove"] = new_remove
        else:
            return b
        return a
