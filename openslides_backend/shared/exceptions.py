class BackendBaseException(Exception):
    """
    Base exception for all custom exceptions of this service.
    """

    def __init__(self, message: str) -> None:
        self.message = message


class AuthenticationException(BackendBaseException):
    pass


class ViewException(BackendBaseException):
    pass


class ActionException(BackendBaseException):
    pass


class PermissionDenied(BackendBaseException):
    pass


class DatabaseException(BackendBaseException):
    pass


class EventStoreException(BackendBaseException):
    pass
