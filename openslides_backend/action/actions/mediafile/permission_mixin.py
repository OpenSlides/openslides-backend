from typing import Any, Dict, Tuple

from ....permissions.management_levels import OrganizationManagementLevel
from ....permissions.permission_helper import has_organization_management_level
from ....services.datastore.commands import GetManyRequest
from ....shared.exceptions import (
    ActionException,
    MissingPermission,
    PermissionException,
)
from ....shared.filters import And, FilterOperator, Not
from ....shared.patterns import KEYSEPARATOR, Collection, FullQualifiedId
from ...action import Action


class MediafilePermissionMixin(Action):
    """
    Mixin to handle the check_permissions of mediafile actions.
    Overwrite check_permissions() and get_meeting_id().
    """

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        collection, id_ = self.get_owner_data(instance)

        # check parent (is_dir and owner)
        if instance.get("parent_id"):
            parent = self.datastore.get(
                FullQualifiedId(self.model.collection, instance["parent_id"]),
                ["is_directory", "owner_id"],
            )
            if not parent.get("is_directory"):
                raise ActionException("Parent is not a directory.")
            if parent.get("owner_id") != str(instance["owner_id"]):
                raise ActionException("Owner and parent don't match.")

        # check (title, parent_id) unique
        if instance.get("title"):
            filter_ = And(
                FilterOperator("title", "=", instance["title"]),
                FilterOperator("parent_id", "=", instance.get("parent_id")),
            )
            if instance.get("id"):
                filter_ = And(
                    filter_, Not(FilterOperator("id", "=", instance.get("id")))
                )
            results = self.datastore.filter(self.model.collection, filter_, ["id"])
            if results:
                raise ActionException(
                    f"Title '{instance['title']}' and parent_id '{instance.get('parent_id')}' are not unique."
                )

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

        # check access groups and owner
        if instance.get("access_group_ids"):
            collection, ids_ = self.get_owner_data(instance)
            gm_request = GetManyRequest(
                Collection("group"), instance["access_group_ids"], ["meeting_id"]
            )
            gm_result = self.datastore.get_many([gm_request])
            groups = gm_result.get(Collection("group"), {}).values()
            for group in groups:
                if group.get("meeting_id") != id_:
                    raise ActionException("Owner and access groups don't match.")

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
