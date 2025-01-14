from ....permissions.permission_helper import has_perm
from ....permissions.permissions import Permission, Permissions
from ....services.database.interface import Database
from ....shared.exceptions import MissingPermission
from ....shared.patterns import KEYSEPARATOR


def check_poll_or_option_perms(
    content_object_id: str,
    datastore: Database,
    user_id: int,
    meeting_id: int,
) -> None:
    if content_object_id.startswith("motion" + KEYSEPARATOR):
        perm: Permission = Permissions.Motion.CAN_MANAGE_POLLS
    elif content_object_id.startswith("assignment" + KEYSEPARATOR):
        perm = Permissions.Assignment.CAN_MANAGE
    else:
        perm = Permissions.Poll.CAN_MANAGE
    if not has_perm(datastore, user_id, perm, meeting_id):
        raise MissingPermission(perm)
