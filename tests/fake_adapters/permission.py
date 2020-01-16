from typing import Any

from openslides_backend.permissions.topic import TOPIC_CAN_MANAGE

TESTDATA = {5968705978: [TOPIC_CAN_MANAGE]}


class PermissionTestAdapter:
    """
    Test adapter for permission queries.

    See openslides_backend.services.providers.PermissionProvier for
    implementation.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    def has_perm(self, user_id: int, permission: str) -> bool:
        return permission in TESTDATA.get(user_id, [])
