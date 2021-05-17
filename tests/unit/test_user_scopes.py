from typing import Any, Dict, List
from unittest import TestCase
from unittest.mock import MagicMock

from openslides_backend.action.actions.user.user_scope_permission_check_mixin import (
    UserScope,
    UserScopePermissionCheckMixin,
)
from openslides_backend.shared.patterns import Collection


class UserScopeTest(TestCase):
    def setUp(self) -> None:
        self.mock_datastore = MagicMock()
        self.mixin = UserScopePermissionCheckMixin(
            MagicMock(), self.mock_datastore, MagicMock(), MagicMock()
        )
        self.mixin.model = MagicMock()

    def set_user_data(self, data: Dict[str, Any]) -> None:
        self.mock_datastore.fetch_model = MagicMock(return_value=data)

    def set_meeting_committees(self, ids: List[int]) -> None:
        return_val = {
            Collection("meeting"): {i: {"committee_id": id} for i, id in enumerate(ids)}
        }
        self.mock_datastore.get_many = MagicMock(return_value=return_val)

    def get_scope(self) -> UserScope:
        return self.mixin.get_user_scope(1)[0]

    def test_no_relations(self) -> None:
        self.set_user_data({})
        assert self.get_scope() == UserScope.Organisation

    def test_single_meeting(self) -> None:
        self.set_user_data({"meeting_ids": [1]})
        assert self.get_scope() == UserScope.Meeting

    def test_multiple_meetings(self) -> None:
        self.set_user_data({"meeting_ids": [1, 2]})
        assert self.get_scope() == UserScope.Organisation

    def test_single_committee_no_meetings(self) -> None:
        self.set_user_data({"committee_ids": [1]})
        assert self.get_scope() == UserScope.Committee

    def test_single_committee_single_related_meeting(self) -> None:
        self.set_user_data({"committee_ids": [1], "meeting_ids": [1]})
        self.set_meeting_committees([1])
        assert self.get_scope() == UserScope.Committee

    def test_single_committee_multiple_related_meetings(self) -> None:
        self.set_user_data({"committee_ids": [1], "meeting_ids": [1, 2]})
        self.set_meeting_committees([1, 1])
        assert self.get_scope() == UserScope.Committee

    def test_single_committee_differing_meeting(self) -> None:
        self.set_user_data({"committee_ids": [1], "meeting_ids": [1]})
        self.set_meeting_committees([2])
        assert self.get_scope() == UserScope.Organisation

    def test_single_committee_mixed_meetings(self) -> None:
        self.set_user_data({"committee_ids": [1], "meeting_ids": [1, 2]})
        self.set_meeting_committees([1, 2])
        assert self.get_scope() == UserScope.Organisation

    def test_multiple_committees_no_meetings(self) -> None:
        self.set_user_data({"committee_ids": [1, 2]})
        assert self.get_scope() == UserScope.Organisation

    def test_multiple_committees_related_meeting(self) -> None:
        self.set_user_data({"committee_ids": [1, 2], "meeting_ids": [1]})
        self.set_meeting_committees([1])
        assert self.get_scope() == UserScope.Organisation

    def test_multiple_committees_differing_meeting(self) -> None:
        self.set_user_data({"committee_ids": [1, 2], "meeting_ids": [1]})
        self.set_meeting_committees([3])
        assert self.get_scope() == UserScope.Organisation
