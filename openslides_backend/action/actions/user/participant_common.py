from typing import Any

from openslides_backend.action.mixins.import_mixins import BaseImportJsonUploadAction
from openslides_backend.permissions.management_levels import (
    CommitteeManagementLevel,
    OrganizationManagementLevel,
)
from openslides_backend.permissions.permissions import Permissions
from openslides_backend.shared.exceptions import MissingPermission
from openslides_backend.shared.patterns import fqid_from_collection_and_id

from ...mixins.import_mixins import ImportRow, ImportState
from ..meeting_user.mixin import CheckLockOutPermissionMixin
from ..user.create_update_permissions_mixin import (
    CreateUpdatePermissionsFailingFields,
    PermissionVarStore,
)


class ParticipantCommon(BaseImportJsonUploadAction, CheckLockOutPermissionMixin):
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

    def validate_locked_out_status(
        self,
        entry: dict[str, Any],
        messages: list[str],
        group_objects: list[dict[str, Any]],
        results: ImportRow | dict[str, Any],
    ) -> None:
        locking_check_instance: dict[str, Any] = {"meeting_id": self.meeting_id}
        if "id" in entry:
            locking_check_instance["id"] = entry["id"]
        if "locked_out" in entry and entry["locked_out"]["info"] != ImportState.REMOVE:
            locking_check_instance["locked_out"] = entry["locked_out"]["value"]
        if len(
            group_ids := [
                id_ for group_object in group_objects if (id_ := group_object.get("id"))
            ]
        ):
            locking_check_instance["group_ids"] = group_ids
        locking_messages = self.check_locking_status(
            self.meeting_id,
            locking_check_instance,
            entry.get("id"),
            raise_exception=False,
        )
        if len(locking_messages):
            results["state"] = ImportState.ERROR
            if (
                "locked_out" in entry
                and entry["locked_out"]["info"] != ImportState.REMOVE
            ):
                entry["locked_out"]["info"] = ImportState.ERROR
            messages.extend(["Error: " + msg[0] for msg in locking_messages])
            if len(
                forbidden_group_ids := {
                    group_id for msg in locking_messages for group_id in msg[1] or []
                }
            ):
                for group_object in group_objects:
                    if group_object.get("id") in forbidden_group_ids:
                        group_object["info"] = ImportState.ERROR
