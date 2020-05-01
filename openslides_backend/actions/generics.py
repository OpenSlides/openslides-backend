from typing import Any, List

from ..shared.exceptions import ActionException, PermissionDenied
from ..shared.interfaces import Event, WriteRequestElement
from ..shared.patterns import FullQualifiedField, FullQualifiedId
from .base import Action, ActionPayload, BaseAction, DataSet


class PermissionMixin(BaseAction):
    """
    Mixin to enable permission check for list of permissions. The permissions
    are concated with OR logic.
    """

    permission_reference = "meeting_id"
    permissions: List[str]

    def check_permission(self, permission_reference_id: int) -> None:
        for manage_permission in self.permissions:
            if self.permission.has_perm(
                self.user_id, f"{permission_reference_id}/{manage_permission}"
            ):
                break
        else:
            raise PermissionDenied(
                f"User must have {' or '.join(self.permissions)} permission for "
                f"{self.permission_reference} {permission_reference_id}."
            )


class CreateAction(PermissionMixin, Action):
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
            # Check permission using permission_reference field.
            self.check_permission(instance[self.permission_reference])

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
            id, position = self.database.getId(collection=self.model.collection)
            self.set_min_position(position)

            # Get relations.
            relations = self.get_relations(
                model=self.model,
                id=id,
                obj=instance,
                relation_fields=relation_fields,
                shortcut=True,
            )

            data.append({"instance": instance, "new_id": id, "relations": relations})

        return {"position": self.position, "data": data}

    def create_instance_write_request_element(
        self, position: int, element: Any
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
            events=[event],
            information=information,
            user_id=self.user_id,
            locked_fields={},
        )


class UpdateAction(PermissionMixin, Action):
    """
    Generic update action.
    """

    def prepare_dataset(self, payload: ActionPayload) -> DataSet:
        """
        Prepares dataset from payload.

        Fetches current db instance to get the correct permission. Then uses the
        input and calculates (reverse) relations.
        """
        if not isinstance(payload, list):
            raise TypeError("ActionPayload for this action must be a list.")

        data = []
        for instance in payload:
            # Fetch current db instance with permission_reference field.
            db_instance, position = self.database.get(
                fqid=FullQualifiedId(self.model.collection, id=instance["id"]),
                mapped_fields=[self.permission_reference],
            )
            self.set_min_position(position)

            # Check permission using permission_reference field.
            self.check_permission(db_instance[self.permission_reference])

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

        return {"position": self.position, "data": data}

    def create_instance_write_request_element(
        self, position: int, element: Any
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
            events=[event],
            information=information,
            user_id=self.user_id,
            locked_fields={
                FullQualifiedField(
                    self.model.collection, element["instance"]["id"], "deleted"
                ): position
            },
        )


class DeleteAction(PermissionMixin, Action):
    """
    Generic delete action.
    """

    def prepare_dataset(self, payload: ActionPayload) -> DataSet:
        """
        Prepares dataset from payload.

        Fetches current db instance to get the correct permission and also all
        reverse relations. If protected reverse relations are not empty, raises
        ActionException. Else uses the input and calculates (reverse) relations
        and that should be removed because on_delete is "cascade".
        """
        if not isinstance(payload, list):
            raise TypeError("ActionPayload for this action must be a list.")

        data = []
        for instance in payload:
            # Fetch current db instance with permission_reference field
            db_instance, position = self.database.get(
                fqid=FullQualifiedId(self.model.collection, id=instance["id"]),
                mapped_fields=[self.permission_reference],
            )
            self.set_min_position(position)

            # Check permission using permission_reference field.
            self.check_permission(db_instance[self.permission_reference])

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

        return {"position": self.position, "data": data}

    def create_instance_write_request_element(
        self, position: int, element: Any
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
            events=[event],
            information=information,
            user_id=self.user_id,
            locked_fields={
                FullQualifiedField(self.model.collection, fqid.id, "deleted"): position
            },
        )
