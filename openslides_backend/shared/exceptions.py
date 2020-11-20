from typing import List

from .patterns import FullQualifiedId


class BackendBaseException(Exception):
    """
    Base exception for all custom exceptions of this service.
    """

    def __init__(self, message: str) -> None:
        self.message = message


class ViewException(BackendBaseException):
    status_code: int


class View400Exception(ViewException):
    status_code = 400


class AuthenticationException(View400Exception):
    pass


class ActionException(View400Exception):
    pass


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


class PermissionException(ServiceException):
    pass


class EventStoreException(View400Exception):
    pass


class PermissionDenied(ViewException):
    status_code = 403
