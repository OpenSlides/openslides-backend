from typing import Any

from ....models.helper import calculate_inherited_groups_helper
from ....services.database.interface import Database
from ....shared.filters import And, FilterOperator, Or
from ....shared.patterns import fqid_from_collection_and_id
from ...action import Action
from ...mixins.meeting_mediafile_helper import find_meeting_mediafile_generate_implicit
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
        meeting_id: int | None = None,
    ) -> ActionData:
        if not meeting_id:
            meeting_id = instance["meeting_id"]
        mediafile = self.datastore.get(
            fqid_from_collection_and_id("mediafile", instance["id"]), ["child_ids"]
        )
        if child_ids := mediafile.get("child_ids"):
            meeting_mediafile_children = self.datastore.filter(
                "meeting_mediafile",
                And(
                    FilterOperator("meeting_id", "=", meeting_id),
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
                    "id",
                ],
            )
            mediafile_id_to_child: dict[int, dict[str, Any]] = {
                m_mediafile["mediafile_id"]: m_mediafile
                for m_mediafile in meeting_mediafile_children.values()
            }
            for child_id in child_ids:
                meeting_mediafile_child: dict[str, Any] = mediafile_id_to_child.get(
                    child_id, {}
                )
                new_instance: dict[str, Any] = {
                    "id": child_id,
                    "meeting_id": meeting_id,
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
                        meeting_id,
                    )


def calculate_inherited_groups_helper_with_parent_id(
    datastore: Database,
    access_group_ids: list[int] | None,
    parent_id: int | None,
    meeting_id: int,
) -> tuple[bool, list[int] | None]:
    if parent_id:
        parent = find_meeting_mediafile_generate_implicit(
            datastore,
            meeting_id,
            parent_id,
            ["is_public", "inherited_access_group_ids"],
        )[1]
    else:
        parent = {}

    return calculate_inherited_groups_helper(
        access_group_ids,
        parent.get("is_public"),
        parent.get("inherited_access_group_ids"),
    )


def calculate_inherited_groups_helper_with_parent_meeting_mediafile_id(
    datastore: Database,
    access_group_ids: list[int] | None,
    parent_meeting_mediafile_id: int | None,
) -> tuple[bool, list[int] | None]:
    if parent_meeting_mediafile_id:
        parent = datastore.get(
            fqid_from_collection_and_id(
                "meeting_mediafile", parent_meeting_mediafile_id
            ),
            ["is_public", "inherited_access_group_ids"],
        )
    else:
        parent = {}

    return calculate_inherited_groups_helper(
        access_group_ids,
        parent.get("is_public"),
        parent.get("inherited_access_group_ids"),
    )
