from typing import List, Optional, Tuple

from ..services.datastore.interface import DatastoreService
from ..shared.patterns import Collection, FullQualifiedId


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


def calculate_inherited_groups_helper_with_parent_id(
    datastore: DatastoreService,
    access_group_ids: Optional[List[int]],
    parent_id: Optional[int],
) -> Tuple[bool, Optional[List[int]]]:
    if parent_id:
        parent = datastore.get(
            FullQualifiedId(Collection("mediafile"), parent_id),
            ["is_public", "inherited_access_group_ids"],
        )
        return calculate_inherited_groups_helper(
            access_group_ids,
            parent.get("is_public"),
            parent.get("inherited_access_group_ids"),
        )
    else:
        return (not bool(access_group_ids), access_group_ids)
