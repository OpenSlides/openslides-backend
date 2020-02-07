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

        Just fetches new id, uses given instance and calculated references.
        """
        if not isinstance(payload, list):
            raise TypeError("ActionPayload for this action must be a list.")
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


class UpdateAction(PermissionMixin, Action):
    """
    Generic update action.
    """

    def prepare_dataset(self, payload: ActionPayload) -> DataSet:
        """
        Prepares dataset from payload.

        Fetches current db instance to get the correct permission. Then uses the
        input and calculated references.
        """
        if not isinstance(payload, list):
            raise TypeError("ActionPayload for this action must be a list.")
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


class DeleteAction(PermissionMixin, Action):
    """
    Generic delete action.
    """

    def prepare_dataset(self, payload: ActionPayload) -> DataSet:
        """
        Prepares dataset from payload.

        Fetches current db instance to get the correct permission and also all
        back references. If protected back references are not empty, raises
        ActionException. Else uses the input and calculated references and
        back references that should be removed because on_delete is "cascade".
        """
        if not isinstance(payload, list):
            raise TypeError("ActionPayload for this action must be a list.")
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
                    if db_instance.get(back_reference_name):
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
