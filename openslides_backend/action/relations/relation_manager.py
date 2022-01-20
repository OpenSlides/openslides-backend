from typing import Any, Dict, List, cast

from ...models.base import Model, model_registry
from ...models.fields import BaseRelationField, BaseTemplateField, Field
from ...services.datastore.interface import DatastoreService
from ...shared.exceptions import ActionException, DatastoreException
from ...shared.patterns import (
    Collection,
    FullQualifiedField,
    FullQualifiedId,
    transform_to_fqids,
)
from ..util.assert_belongs_to_meeting import assert_belongs_to_meeting
from .calculated_field_handler import CalculatedFieldHandlerCall
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
        process_calculated_fields_only: bool = False,
    ) -> RelationUpdates:
        # id has to be provided to be able to correctly update relations
        assert "id" in instance

        if not process_calculated_fields_only:
            self.process_template_fields(model, instance)

        relations: RelationUpdates = {}
        calculated_field_handler_calls: List[CalculatedFieldHandlerCall] = []
        for field_name in instance:
            if not model.has_field(field_name):
                continue
            field = model.get_field(field_name)

            calculated_field_handler_calls.append(
                {
                    "field": field,
                    "field_name": field_name,
                    "instance": instance,
                    "action": action,
                }
            )

            # only relations are handled here
            if not isinstance(field, BaseRelationField):
                continue
            # ignore template fields, we have to do no relation handling there
            if isinstance(field, BaseTemplateField) and field.is_template_field(
                field_name
            ):
                continue

            handler = SingleRelationHandler(
                self.datastore,
                field,
                field_name,
                instance,
            )
            result = handler.perform()
            for fqfield, relations_element in result.items():
                if not process_calculated_fields_only:
                    self.process_relation_element(fqfield, relations_element, relations)

                related_field_name = fqfield.field
                related_model = model_registry[fqfield.collection]()
                related_field = related_model.get_field(related_field_name)
                related_instance = {
                    "id": fqfield.id,
                    related_field_name: relations_element["value"],
                }
                calculated_field_handler_calls.append(
                    {
                        "field": related_field,
                        "field_name": related_field_name,
                        "instance": related_instance,
                        "action": action,
                    }
                )
        if not process_calculated_fields_only:
            self.apply_relation_updates(relations)
        for call in calculated_field_handler_calls:
            self.call_calculated_field_handlers(relations, **call)
        return relations

    def process_template_fields(self, model: Model, instance: Dict[str, Any]) -> None:
        """
        Processes all template fields in the given instance. They must be given as
        objects (mapping replacements to values). The corresponding structured fields
        will be set accordingly.
        """
        additional_instance_fields = {}

        # gather all template fields and structured fields in this instance
        structured_fields = []
        template_fields = []
        for field_name in instance:
            field = model.try_get_field(field_name)
            if not field or not isinstance(field, BaseTemplateField):
                continue

            if field.is_template_field(field_name):
                template_fields.append((field_name, field))
            else:
                structured_fields.append((field_name, field))

        def get_template_field_db_value(template_field_name: str) -> List[str]:
            try:
                return self.datastore.get(
                    fqid=FullQualifiedId(model.collection, instance["id"]),
                    mapped_fields=[template_field_name],
                ).get(template_field_name, [])
            except DatastoreException:
                return []

        def set_structured_field(
            field: BaseTemplateField, replacement: str, value: Any
        ) -> None:
            if (
                isinstance(field, BaseRelationField)
                and field.is_list_field
                and value == []
            ):
                value = None

            template_field_name = field.get_template_field_name()
            structured_field_name = field.get_structured_field_name(replacement)
            additional_instance_fields[structured_field_name] = value
            template_field = additional_instance_fields[template_field_name]

            if value is not None:
                if replacement not in template_field:
                    if field.replacement_collection:
                        # check if the model the replacement is referring to exists
                        self.datastore.fetch_model(
                            fqid=FullQualifiedId(
                                field.replacement_collection, int(replacement)
                            ),
                            mapped_fields=["id"],
                            exception=True,
                        )
                    elif field.replacement_enum:
                        if replacement not in field.replacement_enum:
                            raise ActionException(
                                f"Replacement {replacement} does not exist in field {field.own_field_name}´s replacement_enum."
                            )
                    template_field.append(replacement)

                if field.replacement_collection and isinstance(
                    field, BaseRelationField
                ):
                    # check that the given (fq)ids are valid for this replacement
                    if field.replacement_collection != Collection("meeting"):
                        raise NotImplementedError(
                            "Structured relation fields with a replacement collection other than meeting are not permitted"
                        )

                    fqids = transform_to_fqids(value, field.get_target_collection())
                    assert_belongs_to_meeting(self.datastore, fqids, int(replacement))
            else:
                if replacement in template_field:
                    template_field.remove(replacement)

        # process template fields and set the contained structured fields
        for field_name, field in template_fields:
            field_value = instance[field_name]
            assert isinstance(
                field_value, dict
            ), f"Field '{field_name}' has no dict as value: '{field_value}'"
            additional_instance_fields[field_name] = get_template_field_db_value(
                field_name
            )
            for replacement, value in field_value.items():
                set_structured_field(field, str(replacement), value)

        # process directly given structured fields, overwriting any previous ones
        for field_name, field in structured_fields:
            value = instance[field_name]
            template_field_name = field.get_template_field_name()
            # if this template field wasn't touched before, we have to fetch it from the db
            if template_field_name not in additional_instance_fields:
                additional_instance_fields[
                    template_field_name
                ] = get_template_field_db_value(template_field_name)

            replacement = field.get_replacement(field_name)
            set_structured_field(field, replacement, value)

        instance.update(additional_instance_fields)

    def call_calculated_field_handlers(
        self,
        relations: RelationUpdates,
        instance: Dict[str, Any],
        field: Field,
        field_name: str,
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

    def apply_relation_updates(self, relations: RelationUpdates) -> None:
        """
        Applies all given relations updates to the additional models in the datastore.
        """
        for fqfield, relations_element in relations.items():
            if relations_element["type"] in ("add", "remove"):
                field_update_element = cast(FieldUpdateElement, relations_element)
                self.datastore.update_additional_models(
                    fqfield.fqid, {fqfield.field: field_update_element["value"]}
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
            Not possible and currently not needed.
        """
        # list field is updated, merge updates
        if a["type"] in ("add", "remove"):
            a = cast(FieldUpdateElement, a)
            assert isinstance(a["value"], list)
            new_value: List[Any] = list(a["value"])  # copy list to prevent data leaks
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
