from typing import Any

from ..shared.exceptions import ActionException
from ..shared.interfaces import Event, WriteRequestElement
from ..shared.patterns import FullQualifiedId
from .base import Action, ActionPayload, DataSet


class CreateAction(Action):
    """
    Generic create action.
    """

    def prepare_dataset(self, payload: ActionPayload) -> DataSet:
        """
        Prepares dataset from payload.

        Just fetches new id, uses given instance and calculates (reverse)
        relations.
        """
        if not isinstance(payload, list):
            raise TypeError("ActionPayload for this action must be a list.")

        data = []
        for instance in payload:
            # Update instance (by default this does nothing)
            instance = self.update_instance(instance)

            # Collect relation fields and also check structured_relation. Collect
            # also reverse relation fields.
            relation_fields = []
            for field_name, field in self.model.get_relation_fields():
                if field_name in instance.keys():
                    if field.structured_relation:
                        if instance.get(field.structured_relation) is None:
                            raise ActionException(
                                "You must give both a relation field "
                                "with structured_relation and its corresponding "
                                "foreign key field."
                            )
                    relation_fields.append((field_name, field, False))
            for field_name, field in self.model.get_reverse_relations():
                if field_name in instance.keys():
                    relation_fields.append((field_name, field, True))

            # Get new id.
            id = self.database.reserve_id(collection=self.model.collection)

            # Get relations.
            relations = self.get_relations(
                model=self.model,
                id=id,
                obj=instance,
                relation_fields=relation_fields,
                shortcut=True,
            )

            data.append({"instance": instance, "new_id": id, "relations": relations})

        return {"data": data}

    def create_instance_write_request_element(
        self, element: Any
    ) -> WriteRequestElement:
        """
        Creates a write request element for one instance of the current model.

        Just prepares a write request element with create event for the given
        instance.
        """
        fqid = FullQualifiedId(self.model.collection, element["new_id"])
        information = {fqid: ["Object created"]}
        event = Event(type="create", fqid=fqid, fields=element["instance"])
        return WriteRequestElement(
            events=[event], information=information, user_id=self.user_id
        )


class UpdateAction(Action):
    """
    Generic update action.
    """

    def prepare_dataset(self, payload: ActionPayload) -> DataSet:
        """
        Prepares dataset from payload.

        Uses the input and calculates (reverse) relations.
        """
        if not isinstance(payload, list):
            raise TypeError("ActionPayload for this action must be a list.")

        data = []
        for instance in payload:
            # TODO: Check if instance exists in DB and is not deleted. Ensure that object or meta_deleted field is added to locked_fields.

            # Update instance (by default this does nothing)
            instance = self.update_instance(instance)

            # Collect relation fields and also check structured_relation. Collect
            # also reverse relation fields.
            relation_fields = []
            for field_name, field in self.model.get_relation_fields():
                if field_name in instance.keys():
                    if field.structured_relation:
                        if instance.get(field.structured_relation) is not None:
                            raise ActionException(
                                "You must not try to update both a relation field "
                                "with structured_relation and its corresponding "
                                "foreign key field."
                            )
                    relation_fields.append((field_name, field, False))
            for field_name, field in self.model.get_reverse_relations():
                if field_name in instance.keys():
                    relation_fields.append((field_name, field, True))

            # Get relations.
            relations = self.get_relations(
                model=self.model,
                id=instance["id"],
                obj=instance,
                relation_fields=relation_fields,
            )

            data.append({"instance": instance, "relations": relations})

        return {"data": data}

    def create_instance_write_request_element(
        self, element: Any
    ) -> WriteRequestElement:
        """
        Creates a write request element for one instance of the current model.

        Just prepares a write request element with update event for the given
        instance.
        """
        fqid = FullQualifiedId(self.model.collection, element["instance"]["id"])
        information = {fqid: ["Object updated"]}
        fields = {k: v for k, v in element["instance"].items() if k != "id"}
        event = Event(type="update", fqid=fqid, fields=fields)
        return WriteRequestElement(
            events=[event], information=information, user_id=self.user_id
        )


class DeleteAction(Action):
    """
    Generic delete action.
    """

    def prepare_dataset(self, payload: ActionPayload) -> DataSet:
        """
        Prepares dataset from payload.

        If protected reverse relations are not empty, raises ActionException inside the
        get_relations method. Else uses the input and calculates (reverse) relations.
        """
        # TODO: The relation field flag on_delete = "cascade" is not supported at the moment. Change this

        if not isinstance(payload, list):
            raise TypeError("ActionPayload for this action must be a list.")

        data = []
        for instance in payload:
            # TODO: Check if instance exists in DB and is not deleted. Ensure that meta_deleted field is added to locked_fields.

            # Update instance (by default this does nothing)
            instance = self.update_instance(instance)

            # Collect relation fields and reverse relation fields and also
            # update instance and set all relation fields and reverse relation
            # fields to None.
            relation_fields = []
            for field_name, field in self.model.get_relation_fields():
                instance[field_name] = None
                relation_fields.append((field_name, field, False))

            for field_name, field in self.model.get_reverse_relations():
                instance[field_name] = None
                relation_fields.append((field_name, field, True))

            # Get relations.
            relations = self.get_relations(
                model=self.model,
                id=instance["id"],
                obj=instance,
                relation_fields=relation_fields,
            )

            data.append({"instance": instance, "relations": relations})

        return {"data": data}

    def create_instance_write_request_element(
        self, element: Any
    ) -> WriteRequestElement:
        """
        Creates a write request element for one instance of the current model.

        Just prepares a write request element with delete event for the given
        instance.
        """
        # TODO: Find solution to delete relations with on_delete == "cascade"
        fqid = FullQualifiedId(self.model.collection, element["instance"]["id"])
        information = {fqid: ["Object deleted"]}
        event = Event(type="delete", fqid=fqid)
        return WriteRequestElement(
            events=[event], information=information, user_id=self.user_id
        )
