from openslides_backend.action.mixins.meeting_user_helper import (
    get_groups_from_meeting_user,
    get_meeting_user,
)

from ..services.datastore.commands import GetManyRequest
from ..services.datastore.interface import DatastoreService
from ..shared.exceptions import ActionException, PermissionDenied
from ..shared.patterns import fqid_from_collection_and_id
from .management_levels import OrganizationManagementLevel
from .permissions import Permission, Permissions, permission_parents


def has_perm(
    datastore: DatastoreService, user_id: int, permission: Permission, meeting_id: int
) -> bool:
    meeting = datastore.get(
        fqid_from_collection_and_id("meeting", meeting_id),
        [
            "anonymous_group_id",
            "enable_anonymous",
            "locked_from_inside",
            "committee_id",
        ],
        lock_result=False,
    )
    not_locked_from_editing = not meeting.get("locked_from_inside")
    # anonymous cannot be fetched from db
    if user_id > 0:
        # committeeadmins, orgaadmins and superadmins have all permissions if the meeting isn't locked from the inside
        if not_locked_from_editing and has_committee_management_level(
            datastore,
            user_id,
            meeting["committee_id"],
        ):
            return True

        meeting_user = get_meeting_user(
            datastore, meeting_id, user_id, ["group_ids", "locked_out"]
        )
        if not meeting_user:
            group_ids = []
        elif meeting_user.get("locked_out"):
            return False
        else:
            group_ids = meeting_user.get("group_ids", [])
        if not group_ids:
            return False
    elif user_id == 0:
        # anonymous users are in the anonymous group
        # check if anonymous is allowed
        if not meeting.get("enable_anonymous"):
            raise PermissionDenied(f"Anonymous is not enabled for meeting {meeting_id}")
        if anonymous_group_id := meeting.get("anonymous_group_id"):
            group_ids = [anonymous_group_id]
        else:
            return False
    else:
        return False

    gmr = GetManyRequest(
        "group",
        group_ids,
        ["permissions", "admin_group_for_meeting_id"],
    )
    result = datastore.get_many([gmr], lock_result=False)
    for group in result["group"].values():
        # admins implicitly have all permissions
        if group.get("admin_group_for_meeting_id") == meeting_id:
            return True
        # check if the current group has the needed permission (or a higher one)
        for group_permission in group.get("permissions", []):
            if is_child_permission(permission, group_permission):
                return True
    return False


def is_child_permission(child: Permission, parent: Permission) -> bool:
    """
    Iterate the permission tree (represented in the permissions object) from child to
    parent or until there are no parents anymore
    """
    queue: list[Permission] = [child]
    while queue:
        current = queue.pop()
        if current == parent:
            return True
        parents = permission_parents[current]
        queue.extend(parents)
    return False


def has_organization_management_level(
    datastore: DatastoreService,
    user_id: int,
    expected_level: OrganizationManagementLevel,
) -> bool:
    """Checks wether a user has the minimum necessary OrganizationManagementLevel"""
    if user_id > 0:
        user = datastore.get(
            fqid_from_collection_and_id("user", user_id),
            ["organization_management_level"],
        )
        return expected_level <= OrganizationManagementLevel(
            user.get("organization_management_level")
        )
    return False


def get_failing_committee_management_levels(
    datastore: DatastoreService,
    user_id: int,
    committee_ids: list[int],
) -> list[int]:
    """
    Checks whether a user has CommitteeManagementLevel 'can_manage' for the committees
    in the list and returns the ids of all that fail.
    """
    if user_id > 0:
        user = datastore.get(
            fqid_from_collection_and_id("user", user_id),
            ["organization_management_level", "committee_management_ids"],
            lock_result=False,
            use_changed_models=False,
        )
        if user.get("organization_management_level") in (
            OrganizationManagementLevel.SUPERADMIN,
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
        ):
            return []
        not_trivial = set(committee_ids).difference(
            user.get("committee_management_ids", [])
        )
        if not_trivial:
            committees = datastore.get_many(
                [GetManyRequest("committee", list(not_trivial), ["all_parent_ids"])]
            )["committee"]
            return [
                id_
                for id_, committee in committees.items()
                if not any(
                    parent_id in user.get("committee_management_ids", [])
                    for parent_id in committee.get("all_parent_ids", [])
                )
            ]
    return []


def has_committee_management_level(
    datastore: DatastoreService,
    user_id: int,
    committee_id: int,
) -> bool:
    """
    Checks whether a user has CommitteeManagementLevel 'can_manage'
    in the given committee.
    """
    if user_id > 0:
        user = datastore.get(
            fqid_from_collection_and_id("user", user_id),
            ["organization_management_level", "committee_management_ids"],
            lock_result=False,
            use_changed_models=False,
        )
        if user.get("organization_management_level") in (
            OrganizationManagementLevel.SUPERADMIN,
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
        ):
            return True
        if committee_id in user.get("committee_management_ids", []) or any(
            parent_id in user.get("committee_management_ids", [])
            for parent_id in datastore.get(
                fqid_from_collection_and_id("committee", committee_id),
                ["all_parent_ids"],
            ).get("all_parent_ids", [])
        ):
            return True
    return False


def get_shared_committee_management_levels(
    datastore: DatastoreService,
    user_id: int,
    committee_ids: list[int],
) -> list[int]:
    """Checks wether a user has CommitteeManagementLevel 'can_manage'."""
    if user_id > 0:
        user = datastore.get(
            fqid_from_collection_and_id("user", user_id),
            ["committee_management_ids"],
            lock_result=False,
            use_changed_models=False,
        )
        if user.get("organization_management_level") in (
            OrganizationManagementLevel.SUPERADMIN,
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
        ):
            return committee_ids
        return list(
            set(committee_ids).intersection(user.get("committee_management_ids", []))
        )
    return []


def filter_surplus_permissions(permission_list: list[Permission]) -> list[Permission]:
    reduced_permissions: list[Permission] = []
    for permission in permission_list:
        if any(
            is_child_permission(permission, possible_parent)
            for possible_parent in permission_list
            if possible_parent != permission
        ):
            continue
        elif permission in reduced_permissions:
            continue
        reduced_permissions.append(permission)
    return reduced_permissions


def is_admin(datastore: DatastoreService, user_id: int, meeting_id: int) -> bool:
    meeting = datastore.get(
        fqid_from_collection_and_id("meeting", meeting_id),
        ["admin_group_id", "locked_from_inside"],
        lock_result=False,
    )
    if not meeting.get("locked_from_inside") and has_organization_management_level(
        datastore, user_id, OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
    ):
        return True

    group_ids = get_groups_from_meeting_user(datastore, meeting_id, user_id)
    return bool(group_ids) and meeting["admin_group_id"] in group_ids


anonymous_perms_whitelist: set[Permission] = {
    Permissions.AgendaItem.CAN_SEE,
    Permissions.AgendaItem.CAN_SEE_INTERNAL,
    Permissions.Assignment.CAN_SEE,
    Permissions.ListOfSpeakers.CAN_SEE,
    Permissions.ListOfSpeakers.CAN_SEE_MODERATOR_NOTES,
    Permissions.Mediafile.CAN_SEE,
    Permissions.Meeting.CAN_SEE_AUTOPILOT,
    Permissions.Meeting.CAN_SEE_FRONTPAGE,
    Permissions.Meeting.CAN_SEE_HISTORY,
    Permissions.Meeting.CAN_SEE_LIVESTREAM,
    Permissions.Motion.CAN_SEE,
    Permissions.Motion.CAN_SEE_INTERNAL,
    Permissions.Projector.CAN_SEE,
    Permissions.User.CAN_SEE,
    Permissions.User.CAN_SEE_SENSITIVE_DATA,
    Permissions.Poll.CAN_SEE_PROGRESS,
}


def check_if_perms_are_allowed_for_anonymous(permissions: list[Permission]) -> None:
    if len(forbidden := set(permissions).difference(anonymous_perms_whitelist)):
        raise ActionException(
            f"The following permissions may not be set for the anonymous group: {forbidden}"
        )
