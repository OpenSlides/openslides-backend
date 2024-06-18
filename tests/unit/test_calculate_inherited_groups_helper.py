from unittest import TestCase

from openslides_backend.models.helper import calculate_inherited_groups_helper


class CalculateInheritedGroupsHelperTest(TestCase):
    """
    Test methods of model/helper functions.
    """

    def test_calculate_inherited_groups_helper(self) -> None:
        # set the data for the test in compact form.
        # parameters(3) | result(2):
        # access_groups parent_is_public parent_inheritated_group |
        # is_public inherited_access_groups

        data: list[
            tuple[
                list[int] | None,
                bool | None,
                list[int] | None,
                bool,
                list[int],
            ]
        ] = [
            ([], None, [], True, []),
            ([], True, [], True, []),
            (None, False, None, False, []),
            (None, False, [1], False, [1]),
            ([1], None, None, False, [1]),
            ([1], True, [], False, [1]),
            ([1], False, [], False, []),
            ([1], False, [2], False, []),
            ([1, 2], False, [2, 3], False, [2]),
        ]
        for (
            access_group_ids,
            parent_is_public,
            parent_inherited_access_group_ids,
            result_is_public,
            result_inherited_access_groups,
        ) in data:
            result = calculate_inherited_groups_helper(
                access_group_ids,
                parent_is_public,
                parent_inherited_access_group_ids,
            )
            excepted_result = result_is_public, result_inherited_access_groups
            self.assertEqual(
                result,
                excepted_result,
                f"calculate_inherited_groups_helper({access_group_ids}, {parent_is_public}, {parent_inherited_access_group_ids}) should be equal  {result_is_public} {result_inherited_access_groups}",
            )
