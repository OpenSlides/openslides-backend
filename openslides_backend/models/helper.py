from typing import List, Optional, Tuple


def calculate_inherited_groups_helper(
    access_group_ids: Optional[List[int]],
    parent_is_public: Optional[bool],
    parent_inherited_access_group_ids: Optional[List[int]],
) -> Tuple[bool, List[int]]:
    inherited_access_group_ids: List[int]
    is_public = False
    if parent_inherited_access_group_ids and access_group_ids:
        inherited_access_group_ids = [
            id_ for id_ in access_group_ids if id_ in parent_inherited_access_group_ids
        ]
    elif access_group_ids:
        inherited_access_group_ids = access_group_ids
    elif parent_inherited_access_group_ids:
        inherited_access_group_ids = parent_inherited_access_group_ids
    else:
        is_public = parent_is_public is not False
        inherited_access_group_ids = []
    return is_public, inherited_access_group_ids
