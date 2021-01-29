from unittest import TestCase

from openslides_backend.action.action import merge_write_requests
from openslides_backend.shared.interfaces.event import EventType
from openslides_backend.shared.interfaces.write_request import WriteRequest

from ..util import get_fqid


class ActionBaseTester(TestCase):
    """
    Tests methods of base Action class and also some helper functions.
    """

    # TODO: Write some more unit tests, e.g. that `perform` calls `validate`,
    # `check_permissions` etc., that `validate` uses the given schema and
    # throws an exception etc.

    def setUp(self) -> None:
        self.write_request_1 = WriteRequest(
            events=[
                {
                    "type": EventType.Create,
                    "fqid": get_fqid("collection_Chebie1jie/42"),
                    "fields": {"field_aeXahloPh1": "test_value_lah8chiiLi"},
                }
            ],
            information={
                get_fqid("collection_Chebie1jie/42"): ["Information text laPu7iepei"]
            },
            user_id=1,
            locked_fields={},
        )
        self.write_request_2 = WriteRequest(
            events=[
                {
                    "type": EventType.Delete,
                    "fqid": get_fqid("collection_Chebie1jie/42"),
                    "fields": {"field_ade8neipaiG": "test_value_zeeto6Aine"},
                }
            ],
            information={
                get_fqid("collection_Chebie1jie/42"): ["Information text eesh7thouY"]
            },
            user_id=1,
            locked_fields={},
        )

    def test_merge_write_requests(self) -> None:
        result = merge_write_requests((self.write_request_1, self.write_request_2))
        expected = WriteRequest(
            events=[
                {
                    "type": EventType.Create,
                    "fqid": get_fqid("collection_Chebie1jie/42"),
                    "fields": {"field_aeXahloPh1": "test_value_lah8chiiLi"},
                },
                {
                    "type": EventType.Delete,
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
            locked_fields={},
        )
        self.assertEqual(result, expected)

    def test_merge_write_requests_different_users(self) -> None:
        self.write_request_2.user_id = 5955333405
        with self.assertRaises(ValueError) as context_manager:
            merge_write_requests((self.write_request_1, self.write_request_2))
        self.assertEqual(
            context_manager.exception.args,
            ("You can not merge two write request elements of different users.",),
        )

    def test_merge_write_requests_empty(self) -> None:
        result = merge_write_requests([])
        assert result is None
