from typing import Any

from ....models.helper import calculate_inherited_groups_helper
from ....services.datastore.commands import GetManyRequest
from ....services.datastore.interface import DatastoreService
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
            get_many_request = GetManyRequest(
                "mediafile",
                mediafile["child_ids"],
                [
                    "access_group_ids",
                    "child_ids",
                    "is_public",
                    "inherited_access_group_ids",
                ],
            )
            gm_result = self.datastore.get_many([get_many_request])
            children = gm_result.get("mediafile", {})
            for child_id in children:
                child = children.get(child_id, {})
                new_instance: dict[str, Any] = {"id": child_id}
                (
                    new_instance["is_public"],
                    new_instance["inherited_access_group_ids"],
                ) = calculate_inherited_groups_helper(
                    child.get("access_group_ids", []),
                    parent_is_public,
                    parent_inherited_access_group_ids,
                )

                if (
                    child.get("is_public") != new_instance["is_public"]
                    or child.get("inherited_access_group_ids")
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
) -> tuple[bool, list[int] | None]:
    if parent_id:
        parent = datastore.get(
            fqid_from_collection_and_id("mediafile", parent_id),
            ["is_public", "inherited_access_group_ids"],
        )
    else:
        parent = {}

    return calculate_inherited_groups_helper(
        access_group_ids,
        parent.get("is_public"),
        parent.get("inherited_access_group_ids"),
    )
