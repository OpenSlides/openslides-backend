from typing import Any

from ..shared.exceptions import ActionException, PermissionDenied
from ..shared.interfaces import Event, WriteRequestElement
from ..shared.patterns import FullQualifiedField, FullQualifiedId
from .actions_interface import Payload
from .base import Action, DataSet


class CreateAction(Action):
    """
    Generic create action.
    """

    permission_reference = "meeting_id"
    manage_permission: str

    def check_permission(self, permission_reference_id: int) -> None:
        if not self.permission.has_perm(
            self.user_id, f"{permission_reference_id}/{self.manage_permission}"
        ):
            raise PermissionDenied(
                f"User does not have {self.manage_permission} permission for "
                f"{self.permission_reference} {permission_reference_id}."
            )

    def prepare_dataset(self, payload: Payload) -> DataSet:
        """
        Prepares dataset from payload.

        Just fetches new id, uses given instance and calculated references.
        """
        data = []
        for instance in payload:
            self.check_permission(instance[self.permission_reference])
            id, position = self.database.getId(collection=self.model.collection)
            self.set_min_position(position)
            references = self.get_references(
                model=self.model,
                id=id,
                obj=instance,
                field_names=(
                    field_name
                    for field_name, field in self.model.get_reference_fields()
                ),
            )
            data.append({"instance": instance, "new_id": id, "references": references})
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


class UpdateAction(Action):
    """
    Generic update action.
    """

    permission_reference = "meeting_id"
    manage_permission: str

    def check_permission(self, permission_reference_id: int) -> None:
        if not self.permission.has_perm(
            self.user_id, f"{permission_reference_id}/{self.manage_permission}"
        ):
            raise PermissionDenied(
                f"User does not have {self.manage_permission} permission for "
                f"{self.permission_reference} {permission_reference_id}."
            )

    def prepare_dataset(self, payload: Payload) -> DataSet:
        """
        Prepares dataset from payload.

        Fetches current db instance to get the correct permission. Then uses the
        input and calculated references.
        """
        data = []
        for instance in payload:
            db_instance, position = self.database.get(
                fqid=FullQualifiedId(self.model.collection, id=instance["id"]),
                mapped_fields=[self.permission_reference],
            )
            self.set_min_position(position)
            self.check_permission(db_instance[self.permission_reference])
            references = self.get_references(
                model=self.model,
                id=instance["id"],
                obj=instance,
                field_names=(
                    field_name
                    for field_name, field in self.model.get_reference_fields()
                    if field_name in instance.keys()
                ),
                deletion_possible=True,
            )
            data.append({"instance": instance, "references": references})
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


class DeleteAction(Action):
    """
    Generic delete action.
    """

    permission_reference = "meeting_id"
    manage_permission: str

    def check_permission(self, permission_reference_id: int) -> None:
        if not self.permission.has_perm(
            self.user_id, f"{permission_reference_id}/{self.manage_permission}"
        ):
            raise PermissionDenied(
                f"User does not have {self.manage_permission} permission for "
                f"{self.permission_reference} {permission_reference_id}."
            )

    def prepare_dataset(self, payload: Payload) -> DataSet:
        """
        Prepares dataset from payload.

        Fetches current db instance to get the correct permission and also all
        back references. If protected back references are not empty, raises
        ActionException. Else uses the input and calculated references and
        back references that should be removed because on_delete is "cascade".
        """
        data = []
        for instance in payload:
            mapped_fields = [self.permission_reference] + [
                back_reference_name
                for back_reference_name, _ in self.model.get_back_references()
            ]
            db_instance, position = self.database.get(
                fqid=FullQualifiedId(self.model.collection, id=instance["id"]),
                mapped_fields=mapped_fields,
            )
            self.set_min_position(position)
            self.check_permission(db_instance[self.permission_reference])
            for field_name, _ in self.model.get_reference_fields():
                instance[field_name] = None
            cascade_delete = {}
            for back_reference_name, back_reference in self.model.get_back_references():
                if back_reference.on_delete == "protect":
                    if db_instance[back_reference_name]:
                        text = (
                            f"You are not allowed to delete {self.model.verbose_name} "
                            f"{instance['id']} as long as there are some referenced "
                            f"objects (see {back_reference_name})."
                        )
                        raise ActionException(text)
                else:
                    # back_reference.on_delete == "cascade"
                    cascade_delete[back_reference_name] = db_instance[
                        back_reference_name
                    ]
            references = self.get_references(
                model=self.model,
                id=instance["id"],
                obj=instance,
                field_names=(
                    field_name
                    for field_name, field in self.model.get_reference_fields()
                    if field_name in instance.keys()
                ),
                deletion_possible=True,
            )
            data.append(
                {
                    "instance": instance,
                    "references": references,
                    "cascade_delete": cascade_delete,
                }
            )
        return {"position": self.position, "data": data}

    def create_instance_write_request_element(
        self, position: int, element: Any
    ) -> WriteRequestElement:
        """
        Creates a write request element for one instance of the current model.

        Just prepares a write request element with delete event for the given
        instance.
        """
        # TODO: Delete also back references found in element["cascade_delete"]
        assert element["cascade_delete"] == {}
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
