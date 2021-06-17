from typing import Any, Dict, List, Optional, Tuple

from ....services.datastore.commands import GetManyRequest
from ....shared.patterns import Collection, FullQualifiedId
from ...action import BaseAction
from ...util.typing import ActionData


class MediafileCalculatedFieldsMixin(BaseAction):
    """
    provides calculate_inherited_groups(id)
    """

    def calculate_inherited_groups(
        self,
        access_group_ids: Optional[List[int]],
        parent_is_public: Optional[bool],
        parent_inherited_access_group_ids: Optional[List[int]],
    ) -> Tuple[bool, Optional[List[int]]]:

        parent: Dict[str, Any] = dict()
        parent["inherited_access_group_ids"] = parent_inherited_access_group_ids
        parent["is_public"] = parent_is_public

        if not parent["inherited_access_group_ids"]:
            inherited_access_group_ids = access_group_ids
        elif not access_group_ids:
            inherited_access_group_ids = parent.get("inherited_access_group_ids", [])
        else:
            inherited_access_group_ids = [
                id_
                for id_ in access_group_ids
                if id_ in parent.get("inherited_access_group_ids", [])
            ]
        is_public = not bool(inherited_access_group_ids) and bool(parent["is_public"])
        return is_public, inherited_access_group_ids

    def handle_children(
        self,
        instance: Dict[str, Any],
        parent_is_public: Optional[bool],
        parent_inherited_access_group_ids: Optional[List[int]],
    ) -> ActionData:
        mediafile = self.datastore.get(
            FullQualifiedId(Collection("mediafile"), instance["id"]), ["child_ids"]
        )
        if mediafile.get("child_ids"):
            get_many_request = GetManyRequest(
                Collection("mediafile"),
                mediafile["child_ids"],
                [
                    "access_group_ids",
                    "child_ids",
                    "is_public",
                    "inherited_access_group_ids",
                ],
            )
            gm_result = self.datastore.get_many([get_many_request])
            children = gm_result.get(Collection("mediafile"), {})
            for child_id in children:
                child = children.get(child_id, {})
                new_instance: Dict[str, Any] = {"id": child_id}
                (
                    new_instance["is_public"],
                    new_instance["inherited_access_group_ids"],
                ) = self.calculate_inherited_groups(
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
