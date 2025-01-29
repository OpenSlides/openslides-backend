from ....permissions.permission_helper import has_perm
from ....permissions.permissions import Permission, Permissions
from ....services.datastore.interface import DatastoreService
from ....shared.exceptions import ActionException, MissingPermission
from ....shared.patterns import KEYSEPARATOR, collection_from_fqid


def check_poll_or_option_perms(
    content_object_id: str,
    datastore: DatastoreService,
    user_id: int,
    meeting_id: int,
) -> None:
    if content_object_id.startswith("motion" + KEYSEPARATOR):
        perm: Permission = Permissions.Motion.CAN_MANAGE_POLLS
    elif content_object_id.startswith("assignment" + KEYSEPARATOR):
        perm = Permissions.Assignment.CAN_MANAGE
    elif content_object_id.startswith("topic" + KEYSEPARATOR):
        perm = Permissions.Poll.CAN_MANAGE
    else:
        raise ActionException(
            f"'{collection_from_fqid(content_object_id)}' is not a valid poll collection."
        )
    if not has_perm(datastore, user_id, perm, meeting_id):
        raise MissingPermission(perm)
