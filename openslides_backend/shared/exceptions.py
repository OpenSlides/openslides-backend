from typing import Any, Union

from ..permissions.management_levels import (
    CommitteeManagementLevel,
    OrganizationManagementLevel,
)
from ..permissions.permissions import Permission
from .patterns import FullQualifiedId


class BackendBaseException(Exception):
    """
    Base exception for all custom exceptions of this service.
    """

    message: str

    def __init__(self, message: str) -> None:
        self.message = message


class ViewException(BackendBaseException):
    status_code: int

    def __init__(self, message: str, additional_json: dict[str, Any] = {}) -> None:
        super().__init__(message)
        self.additional_json = additional_json

    def get_json(self) -> dict[str, Any]:
        return {**self.additional_json, "success": False, "message": self.message}


class View400Exception(ViewException):
    status_code = 400


class AuthenticationException(View400Exception):
    pass


class ActionException(View400Exception):
    action_error_index: int | None
    action_data_error_index: int | None

    def get_json(self) -> dict[str, Any]:
        json = super().get_json()
        if hasattr(self, "action_error_index") and self.action_error_index is not None:
            json["action_error_index"] = self.action_error_index
        if (
            hasattr(self, "action_data_error_index")
            and self.action_data_error_index is not None
        ):
            json["action_data_error_index"] = self.action_data_error_index
        return json


class ProtectedModelsException(ActionException):
    fqids: list[FullQualifiedId]

    def __init__(
        self, own_fqid: FullQualifiedId, protected_fqids: list[FullQualifiedId]
    ) -> None:
        self.fqids = protected_fqids
        super().__init__(
            f"You can not delete {own_fqid} because you have to delete the following related models first: {protected_fqids}"
        )


class RequiredFieldsException(ActionException):
    required_fields: list[str]

    def __init__(self, fqid_str: str, required_fields: list[str]) -> None:
        self.required_fields = required_fields
        super().__init__(
            f"{fqid_str}: You try to set following required fields to an empty value: {required_fields}"
        )


class BadCodingException(BackendBaseException):
    """Exception that should only be thrown if something is wrong with the coding"""


class PresenterException(View400Exception):
    pass


class ServiceException(View400Exception):
    pass


class DatabaseException(ServiceException):
    pass


class InvalidFormat(DatabaseException):
    pass

class InvalidData(DatabaseException):
    pass


class RelationException(DatabaseException):
    pass


class ModelDoesNotExist(DatabaseException):
    def __init__(self, fqid: str) -> None:
        super().__init__(f"Model '{fqid}' does not exist.")
        self.fqid = fqid


class ModelExists(DatabaseException):
    def __init__(self, fqid: str) -> None:
        super().__init__(f"Model '{fqid}' exists.")
        self.fqid = fqid


class ModelLocked(DatabaseException):
    def __init__(self, keys: str) -> None:
        super().__init__("")
        self.keys = keys


class InvalidDatastoreState(DatabaseException):
    pass


class DatastoreNotEmpty(DatabaseException):
    pass


class DatastoreConnectionException(DatabaseException):
    pass


class DatastoreLockedException(DatabaseException):
    pass


class PermissionException(ServiceException):
    pass


class MediaServiceException(ServiceException):
    pass


class VoteServiceException(ServiceException):
    pass


class PermissionDenied(ViewException):
    status_code = 403


class ServerError(ViewException):
    status_code = 500


class AnonymousNotAllowed(PermissionDenied):
    def __init__(self, action_name: str) -> None:
        super().__init__(f"Anonymous is not allowed to execute {action_name}")


AnyPermission = Union[Permission, OrganizationManagementLevel, CommitteeManagementLevel]


class MissingPermission(PermissionDenied):
    def __init__(
        self,
        permissions: AnyPermission | dict[AnyPermission, int | set[int]],
    ) -> None:
        if isinstance(permissions, dict):
            to_remove = []
            for permission, id_or_ids in permissions.items():
                if isinstance(id_or_ids, set) and not id_or_ids:
                    to_remove.append(permission)
            for permission in to_remove:
                del permissions[permission]
            self.message = "Missing permission" + self._plural_s(permissions) + ": "
            self.message += " or ".join(
                f"{permission.get_verbose_type()} {permission} in {permission.get_base_model()}{self._plural_s(id_or_ids)} {id_or_ids}"
                for permission, id_or_ids in permissions.items()
            )
        else:
            self.message = f"Missing {permissions.get_verbose_type()}: {permissions}"
        super().__init__(self.message)

    def _plural_s(self, permission_or_id_or_ids: dict | int | set[int]) -> str:
        if (
            isinstance(permission_or_id_or_ids, set)
            or (isinstance(permission_or_id_or_ids, dict))
        ) and len(permission_or_id_or_ids) > 1:
            return "s"
        else:
            return ""
