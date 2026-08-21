from collections import defaultdict
from typing import Any, cast

from psycopg import sql

from openslides_backend.action.mixins.meeting_user_helper import (
    get_groups_from_meeting_user,
    get_meeting_user,
)

from ..models.models import Committee, MeetingUser
from ..services.database.commands import GetManyRequest
from ..services.database.interface import Database
from ..shared.exceptions import ActionException, PermissionDenied
from ..shared.patterns import Collection, Id, fqid_from_collection_and_id
from .management_levels import OrganizationManagementLevel
from .permissions import Permission, Permissions, permission_parents

perm_check_fields_orga: dict[Collection, list[str]] = {
    "user": ["organization_management_level"]
}

perm_check_fields_committee: dict[Collection, list[str]] = {
    "user": [*perm_check_fields_orga["user"], "committee_management_ids"],
    "committee": ["all_parent_ids"],
}

perm_check_fields_meeting: dict[Collection, list[str]] = {
    **perm_check_fields_committee,
    "meeting": [
        "anonymous_group_id",
        "enable_anonymous",
        "locked_from_inside",
        "committee_id",
        "admin_group_id",
    ],
    "group": ["permissions", "admin_group_for_meeting_id"],
    "meeting_user": ["group_ids", "locked_out"],
}

WriteFields = tuple[str, str, str, list[str]]


def get_perm_check_data(
    database: Database,
    perm_check_fields: dict[Collection, list[str]],
    user_id: Id,
    meeting_id: Id | None = None,
    committee_id: Id | None = None,
) -> dict[Collection, dict[Id, dict[str, Any]]]:
    join_statement: sql.SQL | sql.Composed = sql.SQL("user_t AS u")
    where_parts = sql.SQL(f"u.id = {user_id}")
    if user_id > 0:
        select_fields = [
            f"u.{field} as user__{field}"
            for field in ["id", *perm_check_fields["user"]]
            if field != "committee_management_ids"
        ]
    elif not meeting_id:
        return {}
    else:
        select_fields = []
    if "meeting" in perm_check_fields:
        group_id_write_fields = cast(WriteFields, MeetingUser.group_ids.write_fields)
        select_fields.extend(
            [
                *[
                    f"m.{field} as meeting__{field}"
                    for field in ["id", *perm_check_fields["meeting"]]
                ],
                *[
                    (
                        f"array(SELECT unnest(g.{field})::text)"
                        if field == "permissions"
                        else f"g.{field}"
                    )
                    + f" AS group__{field}"
                    for field in ["id", *perm_check_fields["group"]]
                    if field != "admin_group_for_meeting_id"
                ],
            ]
        )
        if user_id > 0:
            select_fields.extend(
                [
                    f"mu.{field} as meeting_user__{field}"
                    for field in ["id", *perm_check_fields["meeting_user"]]
                    if field != "group_ids"
                ]
            )
            join_statement += sql.SQL(f""" FULL OUTER JOIN (
                    meeting_t AS m
                    LEFT JOIN (
                        (
                            group_t AS g JOIN {group_id_write_fields[0]} AS mug ON g.id = mug.{group_id_write_fields[2]}
                        )
                        JOIN meeting_user_t AS mu ON mug.{group_id_write_fields[1]} = mu.id
                    ) ON g.meeting_id = m.id
                ) ON u.id = mu.user_id""")
            where_parts = sql.SQL(
                f"(u.id = {user_id} AND (m.id = {meeting_id} OR m.id IS NULL)) OR (m.id = {meeting_id} AND u.id is NULL)"
            )
        else:
            join_statement = sql.SQL(
                "meeting_t AS m LEFT JOIN group_t AS g ON m.anonymous_group_id = g.id"
            )
            where_parts = sql.SQL(f"m.id = {meeting_id}")
    if user_id > 0 and "committee_management_ids" in perm_check_fields["user"]:
        manager_write_fields = cast(WriteFields, Committee.manager_ids.write_fields)
        parent_write_fields = cast(WriteFields, Committee.all_parent_ids.write_fields)
        base_committee_management_select = f"EXISTS(SELECT a.{manager_write_fields[2]} FROM {manager_write_fields[0]} AS a LEFT JOIN {parent_write_fields[0]} AS b ON a.{manager_write_fields[1]} = b.{parent_write_fields[1]} WHERE a.{manager_write_fields[2]} = u.id "
        if committee_id:
            select_fields.append(
                base_committee_management_select
                + f"AND (a.{manager_write_fields[1]} = {committee_id} OR b.{parent_write_fields[1]} = {committee_id})) AS user__is_committee_manager"
            )
        else:
            if not meeting_id:
                raise ActionException(
                    f"Cannot calculate committee permissions for user/{user_id}: Need either meeting_id or committee_id."
                )
            select_fields.append(
                base_committee_management_select
                + f"AND (a.{manager_write_fields[1]} = m.committee_id OR b.{parent_write_fields[1]} = m.committee_id)) AS user__is_committee_manager"
            )
    select_statement = sql.SQL("""
        {select_fields}
        FROM {join_statement}
        WHERE {conditions}
    """).format(
        select_fields=sql.SQL(", ".join(select_fields)),
        join_statement=join_statement,
        conditions=where_parts,
    )
    result = database.execute_custom_select(select_statement)
    result_data: dict[Collection, dict[Id, dict[str, Any]]] = defaultdict(dict)
    for row in result:
        row_data: dict[Collection, dict[str, Any]] = defaultdict(dict)
        for key, value in row.items():
            collection, field = key.split("__")
            row_data[collection][field] = value
        for collection, model in row_data.items():
            if id_ := model["id"]:
                result_data[collection][id_] = model
    return result_data


def has_perm(
    database: Database, user_id: int, permission: Permission, meeting_id: int
) -> bool:
    if database.enable_changed_models:
        # Legacy clause: Delete once all old-style actions are gone
        perm_data: dict[Collection, dict[Id, dict[str, Any]]] = {}
        meeting = database.get(
            fqid_from_collection_and_id("meeting", meeting_id),
            perm_check_fields_meeting["meeting"],
            lock_result=False,
        )
    else:
        perm_data = get_perm_check_data(
            database, perm_check_fields_meeting, user_id, meeting_id
        )
        meeting = perm_data["meeting"][meeting_id]
    not_locked_from_editing = not meeting.get("locked_from_inside")
    # anonymous cannot be fetched from db
    if user_id > 0:
        # committeeadmins, orgaadmins and superadmins have all permissions if the meeting isn't locked from the inside
        if database.enable_changed_models:
            # Legacy clause: Delete once all old-style actions are gone
            if not_locked_from_editing and has_committee_management_level(
                database,
                user_id,
                meeting["committee_id"],
            ):
                return True
        else:
            if not_locked_from_editing and has_committee_management_level_helper(
                perm_data, user_id
            ):
                return True

        if database.enable_changed_models:
            # Legacy clause: Delete once all old-style actions are gone
            meeting_user = get_meeting_user(
                database, meeting_id, user_id, perm_check_fields_meeting["meeting_user"]
            )
        else:
            if len(meeting_users := perm_data.get("meeting_user", {})) > 1:
                raise ActionException(
                    f"Found multiple meeting_users for meeting {meeting_id} and user {user_id}."
                )
            meeting_user = (
                list(meeting_users.values())[0] if len(meeting_users) else None
            )
        if not meeting_user:
            group_ids = []
        elif meeting_user.get("locked_out"):
            return False
        elif database.enable_changed_models:
            # Legacy clause: Delete once all old-style actions are gone
            group_ids = meeting_user.get("group_ids", [])
        else:
            group_ids = list(perm_data["group"].keys())
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

    if database.enable_changed_models:
        # Legacy clause: Delete once all old-style actions are gone
        gmr = GetManyRequest(
            "group",
            group_ids,
            perm_check_fields_meeting["group"],
        )
        result = database.get_many([gmr], lock_result=False)
        groups = result["group"]
    else:
        groups = perm_data["group"]
    for id_, group in groups.items():
        # admins implicitly have all permissions
        if id_ == meeting["admin_group_id"]:
            return True
        # check if the current group has the needed permission (or a higher one)
        if database.enable_changed_models:
            # Legacy clause: Delete once all old-style actions are gone
            for group_permission in group.get("permissions", []):
                if is_child_permission(permission, group_permission):
                    return True
        else:
            for group_permission in group.get("permissions") or []:
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
    database: Database,
    user_id: int,
    expected_level: OrganizationManagementLevel,
) -> bool:
    """Checks wether a user has the minimum necessary OrganizationManagementLevel"""
    if user_id > 0:
        if database.enable_changed_models:
            # Legacy clause: Delete once all old-style actions are gone
            user = database.get(
                fqid_from_collection_and_id("user", user_id),
                perm_check_fields_orga["user"],
            )
        else:
            user = get_perm_check_data(database, perm_check_fields_orga, user_id)[
                "user"
            ][user_id]
        return expected_level <= OrganizationManagementLevel(
            user.get("organization_management_level", "")
        )
    return False


def get_failing_committee_management_levels(
    datastore: Database,
    user_id: int,
    committee_ids: list[int],
) -> list[int]:
    """
    Checks whether a user committee manager for the committees
    in the list and returns the ids of all that fail.
    """
    if user_id > 0:
        user = datastore.get(
            fqid_from_collection_and_id("user", user_id),
            perm_check_fields_committee["user"],
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
                [
                    GetManyRequest(
                        "committee",
                        list(not_trivial),
                        perm_check_fields_committee["committee"],
                    )
                ]
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
    database: Database,
    user_id: int,
    committee_id: int,
) -> bool:
    """
    Checks whether a user is committee manager in the given committee.
    """
    if not database.enable_changed_models:
        perm_data = get_perm_check_data(
            database, perm_check_fields_committee, user_id, committee_id=committee_id
        )
        return has_committee_management_level_helper(perm_data, user_id)
    # Rest of function is legacy code: Delete once all old-style actions are gone
    if user_id > 0:
        user = database.get(
            fqid_from_collection_and_id("user", user_id),
            perm_check_fields_committee["user"],
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
            for parent_id in database.get(
                fqid_from_collection_and_id("committee", committee_id),
                perm_check_fields_committee["committee"],
            ).get("all_parent_ids", [])
        ):
            return True
    return False


def has_committee_management_level_helper(
    perm_data: dict[Collection, dict[Id, dict[str, Any]]],
    user_id: int,
) -> bool:
    if user_id > 0:
        user = perm_data["user"][user_id]
        if user.get("organization_management_level") in (
            OrganizationManagementLevel.SUPERADMIN,
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
        ):
            return True
        if user["is_committee_manager"]:
            return True
    return False


def get_shared_committee_management_levels(
    datastore: Database,
    user_id: int,
    committee_ids: list[int],
) -> list[int]:
    """
    Checks whether a user is manager in the given committees.
    Returns a list where this is the case or all if the user is orga admin.
    """
    if user_id > 0:
        user = datastore.get(
            fqid_from_collection_and_id("user", user_id),
            perm_check_fields_committee["user"],
            lock_result=False,
            use_changed_models=False,
        )
        if user.get("organization_management_level") in (
            OrganizationManagementLevel.SUPERADMIN,
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
        ):
            return committee_ids
        return list(
            {
                id_
                for committee_id, committee in datastore.get_many(
                    [
                        GetManyRequest(
                            "committee",
                            committee_ids,
                            perm_check_fields_committee["committee"],
                        )
                    ]
                )["committee"].items()
                for id_ in [committee_id, *committee.get("all_parent_ids", [])]
            }.intersection(user.get("committee_management_ids", []))
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


def is_admin(datastore: Database, user_id: int, meeting_id: int) -> bool:
    meeting = datastore.get(
        fqid_from_collection_and_id("meeting", meeting_id),
        perm_check_fields_meeting["meeting"],
        lock_result=False,
    )
    if not meeting.get("locked_from_inside") and has_committee_management_level(
        datastore, user_id, meeting["committee_id"]
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
