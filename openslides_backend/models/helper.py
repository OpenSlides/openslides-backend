from typing import Any, Dict, List, Optional, Tuple


def calculate_inherited_groups_helper(
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
