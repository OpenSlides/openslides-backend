from typing import Any

from openslides_backend.action.mixins.import_mixins import (
    BaseImportJsonUploadAction,
    ImportRow,
    ImportState,
)
from openslides_backend.permissions.management_levels import (
    CommitteeManagementLevel,
    OrganizationManagementLevel,
)
from openslides_backend.permissions.permissions import Permissions
from openslides_backend.shared.exceptions import MissingPermission
from openslides_backend.shared.patterns import fqid_from_collection_and_id

from ....shared.filters import And, FilterOperator, Or
from ..user.create_update_permissions_mixin import (
    CreateUpdatePermissionsFailingFields,
    PermissionVarStore,
)


class ParticipantCommon(BaseImportJsonUploadAction):
    meeting_id: int

    def check_permissions(self, instance: dict[str, Any]) -> None:
        permstore = PermissionVarStore(self.datastore, self.user_id)
        if self.meeting_id not in permstore.user_meetings:
            meeting = self.datastore.get(
                fqid_from_collection_and_id("meeting", self.meeting_id),
                ["committee_id", "locked_from_inside"],
                lock_result=False,
            )
            if meeting.get("locked_from_inside"):
                raise MissingPermission(
                    {
                        Permissions.User.CAN_MANAGE: self.meeting_id,
                    }
                )
            if (
                permstore.user_oml < OrganizationManagementLevel.CAN_MANAGE_USERS
                and self.meeting_id not in permstore.user_committees_meetings
            ):
                raise MissingPermission(
                    {
                        Permissions.User.CAN_MANAGE: self.meeting_id,
                        OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION: 1,
                        CommitteeManagementLevel.CAN_MANAGE: meeting["committee_id"],
                    }
                )

        self.permission_check = CreateUpdatePermissionsFailingFields(
            permstore,
            self.services,
            self.datastore,
            self.relation_manager,
            self.logging,
            self.env,
            self.skip_archived_meeting_check,
            self.use_meeting_ids_for_archived_meeting_check,
        )

    def check_meeting_admin_integrity(
        self, meeting_id: int, rows: list[dict[str, Any]] | list[ImportRow] = []
    ) -> bool:
        update_rows: dict[int, dict[str, Any] | ImportRow] = {
            id_: row for row in rows if (id_ := row["data"].get("id"))
        }
        if not len(update_rows):
            return True
        meeting = self.datastore.get(
            fqid_from_collection_and_id("meeting", meeting_id),
            ["admin_group_id", "template_for_organization_id"],
        )
        if meeting.get("template_for_organization_id"):
            return True
        user_ids_to_group_ids: dict[int, list[int]] = {
            date["data"]["id"]: [
                id_
                for group in date["data"].get("groups", [])
                if (id_ := group.get("id"))
            ]
            for date in update_rows.values()
        }
        create_rows: list[dict[str, Any] | ImportRow] = [
            row for row in rows if not row["data"].get("id")
        ]
        added_groups = {
            group_id
            for group_list in user_ids_to_group_ids.values()
            for group_id in group_list
        }
        added_groups.update(
            {
                group_id
                for create_instance in create_rows
                for group in create_instance["data"].get("groups", [])
                if (group_id := group.get("id"))
            }
        )
        if meeting["admin_group_id"] in added_groups:
            return True
        filters = And(
            FilterOperator("meeting_id", "=", meeting_id),
            Or(
                FilterOperator("user_id", "=", user_id)
                for user_id in user_ids_to_group_ids
            ),
        )
        if len(user_ids_to_group_ids):
            meeting_users = self.datastore.filter(
                "meeting_user", filters, ["group_ids", "user_id"]
            )
            group = self.datastore.get(
                fqid_from_collection_and_id("group", meeting["admin_group_id"]),
                ["id", "meeting_user_ids"],
            )
            if group.get("meeting_user_ids", []) and not any(
                m_user_id not in meeting_users
                for m_user_id in group.get("meeting_user_ids", [])
            ):
                broken_user_ids: set[int] = {
                    m_user["user_id"]
                    for m_user in meeting_users.values()
                    if meeting["admin_group_id"] in (m_user.get("group_ids", []) or [])
                }
                for user_id in broken_user_ids:
                    row = update_rows[user_id]
                    row["state"] = ImportState.ERROR
                    row["messages"].append(
                        "Error: Cannot remove last member of admin group"
                    )
                    row["data"]["groups"].append(
                        {"info": ImportState.ERROR, "value": ""}
                    )
                return False
        return True
