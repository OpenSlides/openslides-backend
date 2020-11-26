from typing import Any, Dict

from ...models.base import Model
from ...models.fields import BaseRelationField
from ...services.datastore.interface import DatastoreService
from ...shared.patterns import FullQualifiedField
from ...shared.typing import ModelMap
from .single_relation_handler import Relations, RelationsElement, SingleRelationHandler


class RelationManager:
    datastore: DatastoreService

    relation_field_updates: Dict[FullQualifiedField, Any]

    def __init__(self, datastore: DatastoreService) -> None:
        self.datastore = datastore
        self.relation_field_updates = {}

    def get_relation_updates(
        self,
        model: Model,
        instance: Dict[str, Any],
        additional_relation_models: ModelMap = {},
    ) -> Dict[FullQualifiedField, RelationsElement]:
        # id has to be provided to be able to correctly update relations
        assert "id" in instance
        relations: Relations = {}
        for field_name in instance:
            if not model.has_field(field_name):
                continue
            field = model.get_field(field_name)
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
                if fqfield not in self.relation_field_updates or not isinstance(
                    relations_element["value"], list
                ):
                    # first time this fqfield is encountered: add it to the dict
                    # OR override of simple field, which is just saved as well
                    self.relation_field_updates[fqfield] = relations_element["value"]
                else:
                    # list field is updated, merge updates
                    if relations_element["type"] == "add":
                        self.relation_field_updates[fqfield].append(
                            relations_element["modified_element"]
                        )
                    else:
                        try:
                            self.relation_field_updates[fqfield].remove(
                                relations_element["modified_element"]
                            )
                        except ValueError:
                            # value was already removed
                            continue
                    relations_element["value"] = self.relation_field_updates[fqfield]
                relations[fqfield] = relations_element
        return relations
