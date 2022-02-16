from typing import Any, Dict, Tuple

from ....permissions.management_levels import OrganizationManagementLevel
from ....permissions.permission_helper import has_organization_management_level
from ....shared.exceptions import (
    ActionException,
    MissingPermission,
    PermissionException,
)
from ....shared.patterns import KEYSEPARATOR, FullQualifiedId
from ...action import Action


class MediafilePermissionMixin(Action):
    """
    Mixin to handle the check_permissions of mediafile actions.
    Overwrite check_permissions() and get_meeting_id().
    """

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        collection, id_ = self.get_owner_data(instance)

        # handle organization permissions
        if collection == "organization":
            self.assert_not_anonymous()
            if "access_group_ids" in instance:
                raise PermissionException(
                    "access_group_ids is not allowed in organization mediafiles."
                )
            if not has_organization_management_level(
                self.datastore,
                self.user_id,
                OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
            ):
                raise MissingPermission(
                    OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
                )
            return

        assert collection == "meeting"

        # check for token, not allowed in meeting.
        if "token" in instance:
            raise PermissionException("token is not allowed in meeting mediafiles.")

        super().check_permissions(instance)

    def check_for_archived_meeting(self, instance: Dict[str, Any]) -> None:
        collection, id_ = self.get_owner_data(instance)
        if collection != "meeting":
            return
        super().check_for_archived_meeting(instance)

    def get_meeting_id(self, instance: Dict[str, Any]) -> int:
        collection, id_ = self.get_owner_data(instance)
        if collection == "meeting":
            return id_
        raise ActionException("Try to get a meeting id from a organization mediafile.")

    def get_owner_data(self, instance: Dict[str, Any]) -> Tuple[str, int]:
        owner_id = instance.get("owner_id")
        if not owner_id:
            mediafile = self.datastore.get(
                FullQualifiedId(self.model.collection, instance["id"]), ["owner_id"]
            )
            owner_id = mediafile["owner_id"]
        collection, id_ = str(owner_id).split(KEYSEPARATOR)
        return collection, int(id_)
