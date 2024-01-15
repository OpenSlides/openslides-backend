from typing import Any, Dict, List, Optional, Union

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

    def __init__(self, message: str, additional_json: Dict[str, Any] = {}) -> None:
        super().__init__(message)
        self.additional_json = additional_json

    def get_json(self) -> Dict[str, Any]:
        return {**self.additional_json, "success": False, "message": self.message}


class View400Exception(ViewException):
    status_code = 400


class AuthenticationException(View400Exception):
    pass


class ActionException(View400Exception):
    action_error_index: Optional[int]
    action_data_error_index: Optional[int]

    def get_json(self) -> Dict[str, Any]:
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
    fqids: List[FullQualifiedId]

    def __init__(
        self, own_fqid: FullQualifiedId, protected_fqids: List[FullQualifiedId]
    ) -> None:
        self.fqids = protected_fqids
        super().__init__(
            f"You can not delete {own_fqid} because you have to delete the following related models first: {protected_fqids}"
        )


class RequiredFieldsException(ActionException):
    required_fields: List[str]

    def __init__(self, fqid_str: str, required_fields: List[str]) -> None:
        self.required_fields = required_fields
        super().__init__(
            f"{fqid_str}: You try to set following required fields to an empty value: {required_fields}"
        )


class PresenterException(View400Exception):
    pass


class ServiceException(View400Exception):
    pass


class DatastoreException(ServiceException):
    pass


class DatastoreConnectionException(DatastoreException):
    pass


class DatastoreLockedException(DatastoreException):
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
        permissions: Union[AnyPermission, Dict[AnyPermission, int]],
    ) -> None:
        if isinstance(permissions, dict):
            self.message = (
                "Missing permission" + ("s" if len(permissions) > 1 else "") + ": "
            )
            self.message += " or ".join(
                f"{permission.get_verbose_type()} {permission} in {permission.get_base_model()} {id}"
                for permission, id in permissions.items()
            )
        else:
            self.message = f"Missing {permissions.get_verbose_type()}: {permissions}"
        super().__init__(self.message)
