from typing import Any

from openslides_backend.shared.permissions.topic import TOPIC_CAN_MANAGE

TESTDATA = {
    5968705978: [
        f"3611987967/{TOPIC_CAN_MANAGE}",
        f"2393342057/{TOPIC_CAN_MANAGE}",
        f"4002059810/{TOPIC_CAN_MANAGE}",
        f"7816466305/{TOPIC_CAN_MANAGE}",
    ],
}


class PermissionTestAdapter:
    """
    Test adapter for permission queries.

    See openslides_backend.adapters.protocols.PermissionProvier for
    implementation.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    def has_perm(self, user_id: int, permission: str) -> bool:
        return permission in TESTDATA.get(user_id, [])
