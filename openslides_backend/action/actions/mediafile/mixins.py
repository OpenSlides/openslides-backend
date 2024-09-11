from typing import Any

from ....permissions.management_levels import OrganizationManagementLevel
from ....permissions.permission_helper import has_organization_management_level
from ....services.datastore.commands import GetManyRequest
from ....shared.exceptions import ActionException, DatastoreException, MissingPermission
from ....shared.filters import And, Filter, FilterOperator, Not
from ....shared.patterns import KEYSEPARATOR, fqid_from_collection_and_id
from ....shared.util import ONE_ORGANIZATION_ID
from ...action import Action
from ..meeting_mediafile.create import MeetingMediafileCreate
from .calculate_mixins import (
    calculate_inherited_groups_helper,
    calculate_inherited_groups_helper_with_parent_id,
)


class MediafileMixin(Action):
    """
    Mixin to handle the check_permissions of mediafile actions.
    Overwrite update_instance(), check_permissions() and get_meeting_id().
    """

    meeting_fields: list[str] = ["meeting_id", "access_group_ids"]

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
            if "access_group_ids" in instance and (
                "meeting_id" not in instance
                or not self.check_implicitly_published(instance, parent_id)
            ):
                raise ActionException(
                    "access_group_ids is not allowed in organization mediafiles."
                )
        else:
            # check for token, not allowed in meeting.
            if "token" in instance:
                raise ActionException("token is not allowed in meeting mediafiles.")
            self.check_access_groups_and_owner(instance.get("access_group_ids"), id_)

        return instance

    def check_implicitly_published(
        self, instance: dict[str, Any], parent_id: int | None
    ) -> bool:
        if (
            "id" in instance
            and self.datastore.get(
                fqid_from_collection_and_id("mediafile", instance["id"]),
                ["published_to_meetings_in_organization_id"],
            ).get("published_to_meetings_in_organization_id")
            == ONE_ORGANIZATION_ID
        ):
            return True
        if not parent_id:
            return False
        return (
            self.datastore.get(
                fqid_from_collection_and_id("mediafile", parent_id),
                ["published_to_meetings_in_organization_id"],
            ).get("published_to_meetings_in_organization_id")
            == ONE_ORGANIZATION_ID
        )

    def check_permissions(self, instance: dict[str, Any]) -> None:
        collection, _ = self.get_owner_data(instance)

        # handle organization permissions
        if collection == "organization":
            self.assert_not_anonymous()
            instance_fields = set(instance.keys())
            instance_fields.discard("id")
            if len(
                instance_fields.difference(self.meeting_fields)
            ) and not has_organization_management_level(
                self.datastore,
                self.user_id,
                OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
            ):
                raise MissingPermission(
                    OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
                )
            if not len(instance_fields.intersection(self.meeting_fields)):
                return
        else:
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
        elif "meeting_id" in instance:
            return instance["meeting_id"]
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
        if parent_id := instance.get("parent_id"):
            parent = self.datastore.get(
                fqid_from_collection_and_id("mediafile", parent_id),
                ["published_to_meetings_in_organization_id"],
            )
            instance["published_to_meetings_in_organization_id"] = parent.get(
                "published_to_meetings_in_organization_id"
            )
        return instance

    def handle_orga_meeting_mediafile_creation(self, instance: dict[str, Any]) -> None:
        if parent_id := instance.get("parent_id"):
            parent_meeting_data = self.datastore.filter(
                "meeting_mediafile",
                FilterOperator("mediafile_id", "=", parent_id),
                ["inherited_access_group_ids", "is_public", "meeting_id"],
            )
            mm_instances: list[dict[str, Any]] = []
            for parent_meeting_mediafile in parent_meeting_data.values():
                mm_instance: dict[str, Any] = {
                    "meeting_id": parent_meeting_mediafile["meeting_id"],
                    "mediafile_id": instance["id"],
                }
                (
                    mm_instance["is_public"],
                    mm_instance["inherited_access_group_ids"],
                ) = calculate_inherited_groups_helper(
                    None,
                    parent_meeting_mediafile.get("is_public"),
                    parent_meeting_mediafile.get("inherited_access_group_ids"),
                )
                mm_instances.append(mm_instance)
            self.execute_other_action(MeetingMediafileCreate, mm_instances)

    def handle_meeting_meeting_mediafile_creation(
        self, meeting_id: int, instance: dict[str, Any]
    ) -> None:
        mm_instance: dict[str, Any] = {
            "meeting_id": meeting_id,
            "mediafile_id": instance["id"],
        }
        if "access_group_ids" in instance:
            mm_instance["access_group_ids"] = instance.pop("access_group_ids")
        (
            mm_instance["is_public"],
            mm_instance["inherited_access_group_ids"],
        ) = calculate_inherited_groups_helper_with_parent_id(
            self.datastore,
            mm_instance.get("access_group_ids"),
            instance.get("parent_id"),
            meeting_id,
        )
        self.execute_other_action(MeetingMediafileCreate, [mm_instance])
