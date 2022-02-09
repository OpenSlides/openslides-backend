from typing import Any, Dict

from ....permissions.management_levels import OrganizationManagementLevel
from ....permissions.permission_helper import has_organization_management_level
from ....shared.exceptions import (
    ActionException,
    MissingPermission,
    PermissionException,
)
from ....shared.patterns import KEYSEPARATOR, Collection, FullQualifiedId
from ...action import Action


class MediafilePermissionMixin(Action):
    """
    Mixin to handle the check_permissions of mediafile actions.
    Overwrite check_permissions() and get_meeting_id().
    """

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        owner_id = instance.get("owner_id")
        if not owner_id:
            mediafile = self.datastore.get(
                FullQualifiedId(self.model.collection, instance["id"]), ["owner_id"]
            )
            owner_id = mediafile["owner_id"]
        collection, id_ = owner_id.split(KEYSEPARATOR)

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

        # check for archived meeting
        fqid = FullQualifiedId(Collection("meeting"), id_)
        meeting = self.datastore.fetch_model(
            fqid,
            ["is_active_in_organization_id", "name"],
        )
        if not meeting.get("is_active_in_organization_id"):
            raise ActionException(
                f'Meeting {meeting.get("name", "")}/{id_} cannot be changed, because it is archived.'
            )

        super().check_permissions(instance)

    def get_meeting_id(self, instance: Dict[str, Any]) -> int:
        owner_id = instance.get("owner_id")
        if not owner_id:
            mediafile = self.datastore.get(
                FullQualifiedId(self.model.collection, instance["id"]), ["owner_id"]
            )
            owner_id = mediafile["owner_id"]
        collection, id_ = owner_id.split(KEYSEPARATOR)
        if collection == "meeting":
            return id_
        raise ActionException("Try to get a meeting id from a organization mediafile.")
