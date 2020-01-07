class BackendBaseException(Exception):
    def __init__(self, message: str) -> None:
        self.message = message


class AuthException(BackendBaseException):
    pass


class MediaTypeException(BackendBaseException):
    pass


class PermissionDenied(BackendBaseException):
    pass


class ActionException(BackendBaseException):
    pass


class EventStoreException(BackendBaseException):
    pass
