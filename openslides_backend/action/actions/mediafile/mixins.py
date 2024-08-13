from typing import Any

from ....permissions.management_levels import OrganizationManagementLevel
from ....permissions.permission_helper import has_organization_management_level
from ....services.datastore.commands import GetManyRequest
from ....shared.exceptions import ActionException, DatastoreException, MissingPermission
from ....shared.filters import And, Filter, FilterOperator, Not
from ....shared.patterns import KEYSEPARATOR, fqid_from_collection_and_id
from ....shared.util import ONE_ORGANIZATION_ID
from ...action import Action


class MediafileMixin(Action):
    """
    Mixin to handle the check_permissions of mediafile actions.
    Overwrite update_instance(), check_permissions() and get_meeting_id().
    """

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        collection, id_ = self.get_owner_data(instance)
        self.check_parent_is_dir_and_owner(
            instance.get("parent_id"), str(instance.get("owner_id"))
        )
        parent_id = instance.get("parent_id")
        if not parent_id:
            try:
                mediafile = self.datastore.get(
                    fqid_from_collection_and_id(self.model.collection, instance["id"]),
                    ["parent_id"],
                )
                parent_id = mediafile.get("parent_id")
            except DatastoreException:
                pass
        self.check_title_parent_unique(
            instance.get("title"),
            parent_id,
            instance.get("id"),
            fqid_from_collection_and_id(collection, id_),
        )

        if collection == "organization":
            self.check_token_unique(instance.get("token"), instance.get("id"))
            if "access_group_ids" in instance:
                raise ActionException(
                    "access_group_ids is not allowed in organization mediafiles."
                )
        else:
            if instance.get("is_published_to_meetings"):
                raise ActionException(
                    "Only organization-owned mediafiles may be published."
                )
            # check for token, not allowed in meeting.
            if "token" in instance:
                raise ActionException("token is not allowed in meeting mediafiles.")
            self.check_access_groups_and_owner(instance.get("access_group_ids"), id_)

        return instance

    def check_permissions(self, instance: dict[str, Any]) -> None:
        collection, _ = self.get_owner_data(instance)

        # handle organization permissions
        if collection == "organization":
            self.assert_not_anonymous()
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
        super().check_permissions(instance)

    def check_for_archived_meeting(self, instance: dict[str, Any]) -> None:
        collection, id_ = self.get_owner_data(instance)
        if collection != "meeting":
            return
        super().check_for_archived_meeting(instance)

    def get_meeting_id(self, instance: dict[str, Any]) -> int:
        collection, id_ = self.get_owner_data(instance)
        if collection == "meeting":
            return id_
        raise ActionException("Try to get a meeting id from a organization mediafile.")

    def get_owner_data(self, instance: dict[str, Any]) -> tuple[str, int]:
        owner_id = instance.get("owner_id")
        if not owner_id:
            mediafile = self.datastore.get(
                fqid_from_collection_and_id(self.model.collection, instance["id"]),
                ["owner_id"],
            )
            owner_id = mediafile["owner_id"]
        collection, id_ = str(owner_id).split(KEYSEPARATOR)
        return collection, int(id_)

    def check_parent_is_dir_and_owner(
        self, parent_id: int | None, owner_id: str
    ) -> None:
        if parent_id:
            parent = self.datastore.get(
                fqid_from_collection_and_id(self.model.collection, parent_id),
                ["is_directory", "owner_id"],
            )
            if not parent.get("is_directory"):
                raise ActionException("Parent is not a directory.")
            if parent.get("owner_id") != owner_id:
                raise ActionException("Owner and parent don't match.")

    def check_title_parent_unique(
        self,
        title: str | None,
        parent_id: int | None,
        id_: int | None,
        owner_id: str,
    ) -> None:
        if title:
            filter_ = And(
                FilterOperator("title", "=", title),
                FilterOperator("parent_id", "=", parent_id),
                FilterOperator("owner_id", "=", owner_id),
            )
            if id_:
                filter_ = And(filter_, Not(FilterOperator("id", "=", id_)))
            results = self.datastore.filter(self.model.collection, filter_, ["id"])
            if results:
                if parent_id:
                    parent = self.datastore.get(
                        fqid_from_collection_and_id(self.model.collection, parent_id),
                        ["title"],
                    )
                    parent_title = parent.get("title", "")
                    raise ActionException(
                        f"File '{title}' already exists in folder '{parent_title}'."
                    )
                else:
                    raise ActionException(
                        f"File '{title}' already exists in the root folder."
                    )

    def check_access_groups_and_owner(
        self, access_group_ids: list[int] | None, meeting_id: int
    ) -> None:
        if access_group_ids:
            gm_request = GetManyRequest("group", access_group_ids, ["meeting_id"])
            gm_result = self.datastore.get_many([gm_request], lock_result=False)
            groups = gm_result.get("group", {}).values()
            for group in groups:
                if group.get("meeting_id") != meeting_id:
                    raise ActionException("Owner and access groups don't match.")

    def check_token_unique(self, token: str | None, id_: int | None) -> None:
        if token:
            filter_: Filter = And(
                FilterOperator("token", "=", token),
                FilterOperator("owner_id", "=", "organization" + KEYSEPARATOR + "1"),
            )
            if id_:
                filter_ = And(
                    filter_,
                    Not(FilterOperator("id", "=", id_)),
                )
            results = self.datastore.filter(self.model.collection, filter_, ["id"])
            if results:
                raise ActionException(f"Token '{token}' is not unique.")


class MediafileCreateMixin(MediafileMixin):
    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        instance = super().update_instance(instance)
        published = (
            ONE_ORGANIZATION_ID if instance.get("is_published_to_meetings") else None
        )
        if not published and (parent_id := instance.get("parent_id")):
            parent = self.datastore.get(
                fqid_from_collection_and_id("mediafile", parent_id),
                ["published_to_meetings_in_organization_id"],
            )
            published = parent.get("published_to_meetings_in_organization_id")
        if published:
            instance["published_to_meetings_in_organization_id"] = published
        return instance


class MediafileUpdateMixin(MediafileMixin):
    pass  # TODO: Write code for updating with publishing, also write specialized code in mediafile.update and -upload
