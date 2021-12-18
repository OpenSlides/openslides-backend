import os

from .exceptions import ServerError

INTERNAL_AUTH_PASSWORD_FILE = "INTERNAL_AUTH_PASSWORD_FILE"
OPENSLIDES_DEVELOPMENT = "OPENSLIDES_DEVELOPMENT"


def is_truthy(value: str) -> bool:
    truthy = ("1", "on", "true")
    falsy = ("0", "off", "false")
    if value.lower() not in truthy + falsy:
        raise ValueError(f"Value must be one off {truthy + falsy}.")
    return value.lower() in truthy


def is_dev_mode() -> bool:
    dev = os.environ.get(OPENSLIDES_DEVELOPMENT, "off")
    return is_truthy(dev)


def get_internal_auth_password() -> str:
    filename = os.environ.get(INTERNAL_AUTH_PASSWORD_FILE)
    if filename:
        with open(filename) as file_:
            return file_.read()
    else:
        raise ServerError("No internal auth password specified.")
