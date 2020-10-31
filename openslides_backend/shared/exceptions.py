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


class PresenterException(View400Exception):
    pass


class DatabaseException(View400Exception):
    pass


class EventStoreException(View400Exception):
    pass


class PermissionDenied(ViewException):
    status_code = 403
