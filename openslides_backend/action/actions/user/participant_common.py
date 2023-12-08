from typing import Any, Dict

from openslides_backend.action.mixins.import_mixins import BaseImportJsonUpload
from openslides_backend.permissions.management_levels import (
    CommitteeManagementLevel,
    OrganizationManagementLevel,
)
from openslides_backend.permissions.permissions import Permissions
from openslides_backend.shared.exceptions import MissingPermission
from openslides_backend.shared.patterns import fqid_from_collection_and_id

from ..user.create_update_permissions_mixin import (
    CreateUpdatePermissionsFailingFields,
    PermissionVarStore,
)


class ParticipantCommon(BaseImportJsonUpload):
    meeting_id: int

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        permstore = PermissionVarStore(self.datastore, self.user_id)
        if (
            self.meeting_id not in permstore.user_meetings
            and permstore.user_oml < OrganizationManagementLevel.CAN_MANAGE_USERS
            and self.meeting_id not in permstore.user_committees_meetings
        ):
            meeting = self.datastore.get(
                fqid_from_collection_and_id("meeting", self.meeting_id),
                ["committee_id"],
                lock_result=False,
            )
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
