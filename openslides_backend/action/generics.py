from collections import defaultdict
from typing import Any, Dict, Iterable, List, Set, Tuple, Type, Union

from ..models.fields import (
    BaseGenericRelationField,
    BaseRelationField,
    BaseTemplateField,
    BaseTemplateRelationField,
    OnDelete,
)
from ..shared.exceptions import ActionException
from ..shared.interfaces.event import Event
from ..shared.interfaces.write_request_element import WriteRequestElement
from ..shared.patterns import FullQualifiedId
from ..shared.typing import DeletedModel, ModelMap
from .action_interface import ActionResponseResultsElement
from .actions_map import actions_map
from .base import Action, ActionPayload, DataSet, merge_write_request_elements


class CreateAction(Action):
    """
    Generic create action.
    """

    def prepare_dataset(self, payload: ActionPayload) -> DataSet:
        return self.create_action_prepare_dataset(payload)

    def create_action_prepare_dataset(self, payload: ActionPayload) -> DataSet:
        """
        Prepares dataset from payload.
        Just fetches new id, uses given instance and calculates (reverse)
        relations.
        """
        data = []
        for instance in self.get_updated_instances(payload):
            # Primary instance manipulation for defaults and extra fields.
            instance = self.set_defaults(instance)
            instance = self.validate_fields(instance)

            # Fetch new id to have it available in update_instance method
            new_id = self.datastore.reserve_id(collection=self.model.collection)
            instance["id"] = new_id

            instance = self.update_instance(instance)
            instance = self.validate_relation_fields(instance)

            # Collect relation fields and also check structured relations and template fields.
            relation_fields = []
            additional_instance_fields: Dict[str, List[str]] = defaultdict(list)
            for field_name, field in self.model.get_fields():
                if isinstance(field, BaseRelationField) and field_name in instance:
                    if field.structured_relation:
                        if instance.get(field.structured_relation[0]) is None:
                            raise ActionException(
                                "You must give both a relation field "
                                "with structured_relation and its corresponding "
                                "foreign key field."
                            )
                    relation_fields.append((field_name, field))
                elif isinstance(field, BaseTemplateField):
                    structured_fields = self.get_structured_fields_in_instance(
                        field_name, field, instance
                    )
                    for instance_field, replacement in structured_fields:
                        if isinstance(field, BaseTemplateRelationField):
                            relation_fields.append((instance_field, field))
                        template_field_name = (
                            field_name[: field.index] + "$" + field_name[field.index :]
                        )
                        additional_instance_fields[template_field_name].append(
                            replacement
                        )
            instance.update(additional_instance_fields)

            # Get relations.
            relations = self.get_relations(
                model=self.model,
                id=new_id,
                obj=instance,
                relation_fields=relation_fields,
                shortcut=True,
            )

            data.append(
                {"instance": instance, "new_id": new_id, "relations": relations}
            )

        return {"data": data}

    def set_defaults(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        for field_name, field in self.model.get_fields():
            if field_name not in instance.keys() and field.default is not None:
                instance[field_name] = field.default
        return instance

    def create_write_request_elements(
        self, dataset: DataSet
    ) -> Iterable[Union[WriteRequestElement, ActionResponseResultsElement]]:
        yield from self.create_action_create_write_request_elements(dataset)

    def create_action_create_write_request_elements(
        self, dataset: DataSet
    ) -> Iterable[Union[WriteRequestElement, ActionResponseResultsElement]]:
        yield from super().create_write_request_elements(dataset)

    def create_instance_write_request_element(
        self, element: Any
    ) -> Iterable[Union[WriteRequestElement, ActionResponseResultsElement]]:
        yield from self.create_action_create_instance_write_request_element(element)

    def create_action_create_instance_write_request_element(
        self, element: Any
    ) -> Iterable[Union[WriteRequestElement, ActionResponseResultsElement]]:
        """
        Creates a write request element for one instance of the current model.

        Just prepares a write request element with create event for the given
        instance.
        """
        fqid = FullQualifiedId(self.model.collection, element["new_id"])
        information = {fqid: ["Object created"]}
        event = Event(type="create", fqid=fqid, fields=element["instance"])
        yield WriteRequestElement(
            events=[event], information=information, user_id=self.user_id
        )
        response_info: ActionResponseResultsElement = {"id": fqid.id}
        yield response_info


class UpdateAction(Action):
    """
    Generic update action.
    """

    def prepare_dataset(self, payload: ActionPayload) -> DataSet:
        return self.update_action_prepare_dataset(payload)

    def update_action_prepare_dataset(self, payload: ActionPayload) -> DataSet:
        """
        Prepares dataset from payload.

        Uses the input and calculates (reverse) relations.
        """
        data = []
        for instance in self.get_updated_instances(payload):
            # TODO: Check if instance exists in DB and is not deleted. Ensure that object or meta_deleted field is added to locked_fields.

            # Primary instance manipulation for defaults and extra fields.
            instance = self.validate_fields(instance)
            instance = self.update_instance(instance)
            instance = self.validate_relation_fields(instance)

            if not isinstance(instance.get("id"), int):
                raise TypeError(
                    f"Instance {instance} of payload must contain integer id."
                )

            # Collect relation fields and also check structured relations and template fields.
            relation_fields = []
            additional_instance_fields: Dict[str, Set[str]] = defaultdict(set)
            for field_name, field in self.model.get_fields():
                if isinstance(field, BaseRelationField) and field_name in instance:
                    if field.structured_relation:
                        if instance.get(field.structured_relation[0]) is not None:
                            raise ActionException(
                                "You must not try to update both a relation field "
                                "with structured_relation and its corresponding "
                                "foreign key field."
                            )
                    relation_fields.append((field_name, field))
                elif isinstance(field, BaseTemplateField):
                    structured_fields = self.get_structured_fields_in_instance(
                        field_name, field, instance
                    )
                    for instance_field, replacement in structured_fields:
                        if isinstance(field, BaseTemplateRelationField):
                            relation_fields.append((instance_field, field))
                        template_field_name = (
                            field_name[: field.index] + "$" + field_name[field.index :]
                        )
                        template_field_db_value = set(
                            self.fetch_model(
                                fqid=FullQualifiedId(
                                    self.model.collection, instance["id"]
                                ),
                                mapped_fields=[template_field_name],
                            ).get(template_field_name, [])
                        )
                        if instance[instance_field]:
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

            # Get relations.
            relations = self.get_relations(
                model=self.model,
                id=instance["id"],
                obj=instance,
                relation_fields=relation_fields,
            )

            data.append({"instance": instance, "relations": relations})

        return {"data": data}

    def validate_relation_fields(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetches missing fields from db for field equality check and removes them after.
        """
        missing_fields = [
            equal_field_name
            for field_name, field in self.model.get_relation_fields()
            if field.equal_fields and field_name in instance
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
        self, dataset: DataSet
    ) -> Iterable[Union[WriteRequestElement, ActionResponseResultsElement]]:
        yield from self.update_action_create_write_request_elements(dataset)

    def update_action_create_write_request_elements(
        self, dataset: DataSet
    ) -> Iterable[Union[WriteRequestElement, ActionResponseResultsElement]]:
        yield from super().create_write_request_elements(dataset)

    def create_instance_write_request_element(
        self, element: Any
    ) -> Iterable[Union[WriteRequestElement, ActionResponseResultsElement]]:
        yield from self.update_action_create_instance_write_request_element(element)

    def update_action_create_instance_write_request_element(
        self, element: Any
    ) -> Iterable[Union[WriteRequestElement, ActionResponseResultsElement]]:
        """
        Creates a write request element for one instance of the current model.

        Just prepares a write request element with update event for the given
        instance.
        """
        fqid = FullQualifiedId(self.model.collection, element["instance"]["id"])
        information = {fqid: ["Object updated"]}
        fields = {
            k: v
            for k, v in element["instance"].items()
            if k != "id" and not k.startswith("meta_")
        }
        event = Event(type="update", fqid=fqid, fields=fields)
        yield WriteRequestElement(
            events=[event], information=information, user_id=self.user_id
        )


class DeleteAction(Action):
    """
    Generic delete action.
    """

    additional_write_requests: List[WriteRequestElement]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.additional_write_requests = []

    def prepare_dataset(self, payload: ActionPayload) -> DataSet:
        return self.delete_action_prepare_dataset(payload)

    def delete_action_prepare_dataset(self, payload: ActionPayload) -> DataSet:
        """
        Prepares dataset from payload.

        If protected reverse relations are not empty, raises ActionException inside the
        get_relations method. Else uses the input and calculates (reverse) relations.
        """

        data = []
        for instance in self.get_updated_instances(payload):
            # TODO: Check if instance exists in DB and is not deleted. Ensure that meta_deleted field is added to locked_fields.

            # Update instance (by default this does nothing)
            instance = self.update_instance(instance)

            # Fetch db instance with all relevant fields
            relevant_fields = [
                field_name
                for field_name, field in self.model.get_relation_fields()
                if field.on_delete != OnDelete.SET_NULL
            ]
            this_fqid = FullQualifiedId(self.model.collection, instance["id"])
            db_instance = self.datastore.get(
                fqid=this_fqid,
                mapped_fields=relevant_fields,
                lock_result=True,
            )

            # Collect relation fields and also update instance and set
            # all relation fields to None.
            relation_fields: List[Tuple[str, BaseRelationField]] = []
            # Gather all delete actions with payload and also all models to be deleted
            delete_actions: List[Tuple[Type[Action], ActionPayload]] = []
            additional_relation_models: ModelMap = {this_fqid: DeletedModel()}
            for field_name, field in self.model.get_relation_fields():
                if field.structured_relation or field.structured_tag:
                    # TODO: We do not fully support these fields. So silently skip them.
                    continue
                # Check on_delete.
                if field.on_delete != OnDelete.SET_NULL:
                    if isinstance(field, BaseTemplateRelationField):
                        # We currently do not support such template fields.
                        raise NotImplementedError

                    # Extract all foreign keys as fqids from the model
                    foreign_fqids = db_instance.get(field_name, [])
                    if not isinstance(foreign_fqids, list):
                        foreign_fqids = [foreign_fqids]
                    if not isinstance(field, BaseGenericRelationField):
                        assert not isinstance(field.to, list)
                        foreign_fqids = [
                            FullQualifiedId(field.to, id) for id in foreign_fqids
                        ]

                    if field.on_delete == OnDelete.PROTECT:
                        for fqid in foreign_fqids:
                            if not isinstance(
                                self.additional_relation_models.get(fqid), DeletedModel
                            ):
                                raise ActionException(
                                    f"You can not delete {self.model} with id {instance['id']}, "
                                    f"because you have to delete the related model {fqid} first."
                                )
                    else:
                        # field.on_delete == OnDelete.CASCADE
                        # Extract all foreign keys as fqids from the model
                        value = db_instance.get(field_name, [])
                        foreign_fqids = self.get_field_value_as_fqid_list(field, value)

                        # Execute the delete action for all fqids
                        for fqid in foreign_fqids:
                            delete_action_class = actions_map.get(
                                f"{str(fqid.collection)}.delete"
                            )
                            if not delete_action_class:
                                raise ActionException(
                                    f"Can't cascade the delete action to {str(fqid.collection)} "
                                    "since no delete action was found."
                                )
                            # Assume that the delete action uses the standard payload
                            payload = [{"id": fqid.id}]
                            delete_actions.append((delete_action_class, payload))
                            additional_relation_models[fqid] = DeletedModel()
                else:
                    # field.on_delete == OnDelete.SET_NULL
                    if isinstance(field, BaseTemplateRelationField):
                        raw_field_name = (
                            field_name[: field.index] + "$" + field_name[field.index :]
                        )
                        db_instance = self.datastore.get(
                            fqid=FullQualifiedId(self.model.collection, instance["id"]),
                            mapped_fields=[raw_field_name],
                            lock_result=True,
                        )
                        for replacement in db_instance.get(raw_field_name, []):
                            structured_field_name = (
                                field_name[: field.index]
                                + replacement
                                + field_name[field.index :]
                            )
                            instance[structured_field_name] = None
                            relation_fields.append((structured_field_name, field))
                    else:
                        instance[field_name] = None
                        relation_fields.append((field_name, field))

            # Add additional relation models and execute all previously gathered delete actions
            for delete_action_class, payload in delete_actions:
                self.additional_write_requests.extend(
                    self.execute_other_action(
                        delete_action_class, payload, additional_relation_models
                    )
                )

            # Get relations.
            relations = self.get_relations(
                model=self.model,
                id=instance["id"],
                obj=instance,
                relation_fields=relation_fields,
            )

            data.append({"instance": instance, "relations": relations})

        return {"data": data}

    def create_write_request_elements(
        self, dataset: DataSet
    ) -> Iterable[Union[WriteRequestElement, ActionResponseResultsElement]]:
        yield from self.delete_action_create_write_request_elements(dataset)

    def delete_action_create_write_request_elements(
        self, dataset: DataSet
    ) -> Iterable[Union[WriteRequestElement, ActionResponseResultsElement]]:
        items = super().create_write_request_elements(dataset)
        # Pre-yield non write request elements, i. e. action response results elements.
        write_request_elements = []
        for item in items:
            if not isinstance(item, WriteRequestElement):
                yield item
            else:
                write_request_elements.append(item)
        write_request_element = merge_write_request_elements(
            self.additional_write_requests + write_request_elements
        )
        # Remove double entries and updates for deleted models
        events: List[Event] = []
        deleted: List[FullQualifiedId] = []
        for event in write_request_element.events:
            if event["fqid"] in deleted:
                continue
            if event["type"] == "delete":
                deleted.append(event["fqid"])
            events.append(event)
        write_request_element.events = events

        # Finally yield the merged write request element.
        yield write_request_element

    def create_instance_write_request_element(
        self, element: Any
    ) -> Iterable[Union[WriteRequestElement, ActionResponseResultsElement]]:
        yield from self.delete_action_create_instance_write_request_element(element)

    def delete_action_create_instance_write_request_element(
        self, element: Any
    ) -> Iterable[Union[WriteRequestElement, ActionResponseResultsElement]]:
        """
        Creates a write request element for one instance of the current model.

        Just prepares a write request element with delete event for the given
        instance.
        """
        fqid = FullQualifiedId(self.model.collection, element["instance"]["id"])
        information = {fqid: ["Object deleted"]}
        event = Event(type="delete", fqid=fqid)
        yield WriteRequestElement(
            events=[event], information=information, user_id=self.user_id
        )
