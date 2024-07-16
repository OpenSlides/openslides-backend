import pytest

from tests.system.action.base import BaseActionTestCase


@pytest.mark.skip(reason="During development of relational DB not necessary")
class BasePollTestCase(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.vote_service.clear_all()
