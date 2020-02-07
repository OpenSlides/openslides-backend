from typing import Any, List

from openslides_backend.shared.permissions.committee import COMMITTEE_CAN_MANAGE
from openslides_backend.shared.permissions.meeting import MEETING_CAN_MANAGE
from openslides_backend.shared.permissions.motion import (
    MOTION_CAN_MANAGE,
    MOTION_CAN_MANAGE_METADATA,
)
from openslides_backend.shared.permissions.topic import TOPIC_CAN_MANAGE

TESTDATA = {
    5968705978: [
        f"3611987967/{TOPIC_CAN_MANAGE}",
        f"2393342057/{TOPIC_CAN_MANAGE}",
        f"4002059810/{TOPIC_CAN_MANAGE}",
        f"7816466305/{TOPIC_CAN_MANAGE}",
    ],
    7121641734: [f"5914213969/{MEETING_CAN_MANAGE}"],
    7668157706: [f"1/{COMMITTEE_CAN_MANAGE}"],
    7826715669: [f"5562405520/{MOTION_CAN_MANAGE}"],
    3265963568: [f"5562405520/{MOTION_CAN_MANAGE_METADATA}"],
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

    def get_all(self, user_id: int) -> List[str]:
        return TESTDATA.get(user_id, [])
