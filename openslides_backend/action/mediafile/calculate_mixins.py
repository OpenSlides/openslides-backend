from typing import Any, Dict, List, Optional, Tuple

from ..base import BaseAction


class MediafileCalculatedFieldsMixin(BaseAction):
    """
    provides calculate_inherited_groups(id)
    """

    def calculate_inherited_groups(
        self,
        id_: int,
        access_group_ids: List[int],
        parent_has_inherited_access_groups: Optional[bool],
        parent_inherited_access_group_ids: Optional[List[int]],
    ) -> Tuple[bool, List[int]]:

        parent: Dict[str, Any] = dict()
        parent["inherited_access_group_ids"] = parent_inherited_access_group_ids
        parent["has_inherited_access_groups"] = parent_has_inherited_access_groups

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
        has_inherited_access_groups = bool(inherited_access_group_ids) or bool(
            parent["has_inherited_access_groups"]
        )
        return has_inherited_access_groups, inherited_access_group_ids
