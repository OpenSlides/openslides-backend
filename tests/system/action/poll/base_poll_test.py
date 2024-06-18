from tests.system.action.base import BaseActionTestCase


class BasePollTestCase(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.vote_service.clear_all()
