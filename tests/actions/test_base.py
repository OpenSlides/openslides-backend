from unittest import TestCase

from openslides_backend.actions.base import merge_write_request_elements
from openslides_backend.shared.interfaces import WriteRequestElement

from ..utils import get_fqfield, get_fqid


class ActionsBaseTester(TestCase):
    """
    Tests methods of base Action class and also some helper functions.
    """

    def setUp(self) -> None:
        self.write_request_element_1 = WriteRequestElement(
            events=[
                {
                    "type": "create",
                    "fqid": get_fqid("collection_Chebie1jie/42"),
                    "fields": {"field_aeXahloPh1": "test_value_lah8chiiLi"},
                }
            ],
            information={
                get_fqid("collection_Chebie1jie/42"): ["Information text laPu7iepei"]
            },
            user_id=1,
            locked_fields={get_fqfield("collection_Chebie1jie/42/field_aeXahloPh1"): 1},
        )
        self.write_request_element_2 = WriteRequestElement(
            events=[
                {
                    "type": "update",
                    "fqid": get_fqid("collection_Chebie1jie/42"),
                    "fields": {"field_ade8neipaiG": "test_value_zeeto6Aine"},
                }
            ],
            information={
                get_fqid("collection_Chebie1jie/42"): ["Information text eesh7thouY"]
            },
            user_id=1,
            locked_fields={get_fqfield("collection_Chebie1jie/42/field_aeXahloPh1"): 2},
        )

    def test_merge_write_request_elements(self) -> None:
        result = merge_write_request_elements(
            (self.write_request_element_1, self.write_request_element_2)
        )
        expected = WriteRequestElement(
            events=[
                {
                    "type": "create",
                    "fqid": get_fqid("collection_Chebie1jie/42"),
                    "fields": {"field_aeXahloPh1": "test_value_lah8chiiLi"},
                },
                {
                    "type": "update",
                    "fqid": get_fqid("collection_Chebie1jie/42"),
                    "fields": {"field_ade8neipaiG": "test_value_zeeto6Aine"},
                },
            ],
            information={
                get_fqid("collection_Chebie1jie/42"): [
                    "Information text laPu7iepei",
                    "Information text eesh7thouY",
                ]
            },
            user_id=1,
            locked_fields={get_fqfield("collection_Chebie1jie/42/field_aeXahloPh1"): 1},
        )
        self.assertEqual(result, expected)

    def test_merge_write_request_elements_different_users(self) -> None:
        self.write_request_element_2["user_id"] = 5955333405
        with self.assertRaises(ValueError) as context_manager:
            merge_write_request_elements(
                (self.write_request_element_1, self.write_request_element_2)
            )
        self.assertEqual(
            context_manager.exception.args,
            ("You can not merge two write request elements of different users.",),
        )
