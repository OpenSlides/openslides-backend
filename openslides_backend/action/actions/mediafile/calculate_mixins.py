from typing import Any

from ....models.helper import calculate_inherited_groups_helper
from ....services.datastore.interface import DatastoreService
from ....shared.filters import And, FilterOperator, Or
from ....shared.patterns import fqid_from_collection_and_id
from ...action import Action
from ...util.typing import ActionData


class MediafileCalculatedFieldsMixin(Action):
    """
    provides calculate_inherited_groups(id)
    """

    def handle_children(
        self,
        instance: dict[str, Any],
        parent_is_public: bool | None,
        parent_inherited_access_group_ids: list[int] | None,
    ) -> ActionData:
        mediafile = self.datastore.get(
            fqid_from_collection_and_id("mediafile", instance["id"]), ["child_ids"]
        )
        if mediafile.get("child_ids"):
            meeting_mediafile_children = self.datastore.filter(
                "meeting_mediafile",
                And(
                    FilterOperator("meeting_id", "=", instance["meeting_id"]),
                    Or(
                        FilterOperator("mediafile_id", "=", child_id)
                        for child_id in mediafile["child_ids"]
                    ),
                ),
                [
                    "access_group_ids",
                    "inherited_access_group_ids",
                    "is_public",
                    "mediafile_id",
                ],
            )
            for meeting_mediafile_child_id in meeting_mediafile_children:
                meeting_mediafile_child = meeting_mediafile_children.get(
                    meeting_mediafile_child_id, {}
                )
                child_id = meeting_mediafile_child["mediafile_id"]
                new_instance: dict[str, Any] = {
                    "id": child_id,
                    "meeting_id": instance["meeting_id"],
                }
                (
                    new_instance["is_public"],
                    new_instance["inherited_access_group_ids"],
                ) = calculate_inherited_groups_helper(
                    meeting_mediafile_child.get("access_group_ids", []),
                    parent_is_public,
                    parent_inherited_access_group_ids,
                )

                if (
                    meeting_mediafile_child.get("is_public")
                    != new_instance["is_public"]
                    or meeting_mediafile_child.get("inherited_access_group_ids")
                    != new_instance["inherited_access_group_ids"]
                ):
                    yield new_instance
                    yield from self.handle_children(
                        new_instance,
                        new_instance["is_public"],
                        new_instance["inherited_access_group_ids"],
                    )


def calculate_inherited_groups_helper_with_parent_id(
    datastore: DatastoreService,
    access_group_ids: list[int] | None,
    parent_id: int | None,
    meeting_id: int,
) -> tuple[bool, list[int] | None]:
    if parent_id:
        parents = datastore.filter(
            "meeting_mediafile",
            And(
                FilterOperator("meeting_id", "=", meeting_id),
                FilterOperator("mediafile_id", "=", parent_id),
            ),
            ["is_public", "inherited_access_group_ids"],
        )
        if len(parents):
            assert len(parents) == 1
            parent = list(parents.values())[0]
        else:
            parent = {}
    else:
        parent = {}

    return calculate_inherited_groups_helper(
        access_group_ids,
        parent.get("is_public"),
        parent.get("inherited_access_group_ids"),
    )


def calculate_inherited_groups_helper_with_parent_meeting_mediafile_id(
    datastore: DatastoreService,
    access_group_ids: list[int] | None,
    parent_id: int | None,
) -> tuple[bool, list[int] | None]:
    if parent_id:
        parent = datastore.get(
            fqid_from_collection_and_id("meeting_mediafile", parent_id),
            ["is_public", "inherited_access_group_ids"],
        )
    else:
        parent = {}

    return calculate_inherited_groups_helper(
        access_group_ids,
        parent.get("is_public"),
        parent.get("inherited_access_group_ids"),
    )
