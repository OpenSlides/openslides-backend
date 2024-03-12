from base64 import b64encode

from openslides_backend.http.views.action_view import INTERNAL_AUTHORIZATION_HEADER
from openslides_backend.shared.env import DEV_PASSWORD


def b64encodes(value: str) -> str:
    """Returns the base64 encoded value as a string."""
    return b64encode(value.encode()).decode()


def get_internal_auth_header(password: str = DEV_PASSWORD) -> dict[str, str]:
    """Returns the internal auth header."""
    return {INTERNAL_AUTHORIZATION_HEADER: b64encodes(password)}
