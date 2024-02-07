def calculate_inherited_groups_helper(
    access_group_ids: list[int] | None,
    parent_is_public: bool | None,
    parent_inherited_access_group_ids: list[int] | None,
) -> tuple[bool, list[int]]:
    inherited_access_group_ids: list[int]
    is_public = False
    if parent_inherited_access_group_ids and access_group_ids:
        inherited_access_group_ids = [
            id_ for id_ in access_group_ids if id_ in parent_inherited_access_group_ids
        ]
    elif access_group_ids:
        if parent_is_public is False:
            inherited_access_group_ids = []
        else:
            inherited_access_group_ids = access_group_ids
    elif parent_inherited_access_group_ids:
        inherited_access_group_ids = parent_inherited_access_group_ids
    else:
        is_public = parent_is_public is not False
        inherited_access_group_ids = []
    return is_public, inherited_access_group_ids
