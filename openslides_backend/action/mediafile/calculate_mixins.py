from typing import List, Tuple

from ...shared.patterns import Collection, FullQualifiedId
from ..base import BaseAction


class MediafileCalculatedFieldsMixin(BaseAction):
    """
    provides calculate_inherited_groups(id)
    """

    def calculate_inherited_groups(
        self, id_: int, access_group_ids: List[int]
    ) -> Tuple[bool, List[int]]:
        mediafile = self.database.get(
            FullQualifiedId(Collection("mediafile"), id_), ["parent_id"]
        )
        if mediafile.get("parent_id") is not None:
            parent = self.database.get(
                FullQualifiedId(Collection("mediafile"), mediafile["parent_id"]),
                ["inherited_access_group_ids", "has_inherited_access_groups"],
            )
            if not parent.get("inherited_access_group_ids"):
                inherited_access_group_ids = access_group_ids
            elif not access_group_ids:
                inherited_access_group_ids = parent["inherited_access_group_ids"]
            else:
                inherited_access_group_ids = [
                    id_
                    for id_ in access_group_ids
                    if id_ in parent["inherited_access_group_ids"]
                ]
            has_inherited_access_groups = bool(inherited_access_group_ids) or bool(
                parent.get("has_inherited_access_groups", False)
            )
        else:
            inherited_access_group_ids = access_group_ids
            has_inherited_access_groups = bool(inherited_access_group_ids)
        return has_inherited_access_groups, inherited_access_group_ids
