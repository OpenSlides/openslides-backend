from typing import Any

from ..shared.exceptions import PermissionDenied
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
                f"User does not have {self.manage_permission} permission for {self.permission_reference} {permission_reference_id}."
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
        fqfields = {}
        for field_name, value in element["instance"].items():
            fqfields[
                FullQualifiedField(self.model.collection, element["new_id"], field_name)
            ] = value
        information = {
            FullQualifiedId(self.model.collection, element["new_id"]): [
                "Object created"
            ]
        }
        event = Event(type="create", fqfields=fqfields)
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
                f"User does not have {self.manage_permission} permission for {self.permission_reference} {permission_reference_id}."
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
        fqfields = {}
        for field_name, value in element["instance"].items():
            if field_name == "id":
                continue
            fqfields[
                FullQualifiedField(
                    self.model.collection, element["instance"]["id"], field_name
                )
            ] = value
        information = {
            FullQualifiedId(self.model.collection, element["instance"]["id"]): [
                "Object updated"
            ]
        }
        event = Event(type="update", fqfields=fqfields)
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
