from typing import List, Optional, Tuple
from unittest import TestCase

from openslides_backend.models.helper import calculate_inherited_groups_helper


class ModelHelper(TestCase):
    """
    Test methods of model/helper functions.
    """

    def test_calculate_inherited_groups_helper(self) -> None:
        # access_groups parent_is_public parent_inheritated_group | is_public
        # inherited_access_groups
        data: List[
            Tuple[
                Optional[List[int]],
                Optional[bool],
                Optional[List[int]],
                bool,
                List[int],
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
        for entry in data:
            self.assertEqual(
                calculate_inherited_groups_helper(entry[0], entry[1], entry[2]),
                (entry[3], entry[4]),
                f"{entry[0]} {entry[1]} {entry[2]} | {entry[3]} {entry[4]}"
            )
