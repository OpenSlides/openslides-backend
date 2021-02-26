from typing import Any, Dict, List, Optional

from .patterns import FullQualifiedId


class BackendBaseException(Exception):
    """
    Base exception for all custom exceptions of this service.
    """

    def __init__(self, message: str) -> None:
        self.message = message


class ViewException(BackendBaseException):
    status_code: int

    def get_json(self) -> Dict[str, Any]:
        return {"success": False, "message": self.message}


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
        self.message = f"You can not delete {own_fqid} because you have to delete the following related models first: {protected_fqids}"


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


class PermissionDenied(ViewException):
    status_code = 403
