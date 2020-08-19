class HttpError(Exception):
    def __init__(self, message, status_code):
        self.message = message
        self.status_code = status_code
        super().__init__(self)


class ServerError(HttpError):
    def __init__(self, message):
        super().__init__(message, 500)


class NotFoundError(HttpError):
    def __init__(self, message="Not Found."):
        super().__init__(message, 404)


class BadRequestError(HttpError):
    def __init__(self, message):
        super().__init__(message, 400)
