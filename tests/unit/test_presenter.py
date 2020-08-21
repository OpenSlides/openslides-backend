from unittest import TestCase
from unittest.mock import MagicMock

from openslides_backend.presenter import PresenterBlob
from openslides_backend.presenter.presenter import PresenterHandler
from openslides_backend.shared.exceptions import PresenterException


class GeneralPresenterTester(TestCase):
    # TODO: more unit tests, e.g. with right key etc.
    def setUp(self) -> None:
        self.presenter_handler = PresenterHandler(
            logging=MagicMock(), services=MagicMock(),
        )
        self.user_id = 0

    def test_with_bad_key(self) -> None:
        payload = [PresenterBlob(presenter="non_existing_presenter", data={})]
        with self.assertRaises(PresenterException) as context_manager:
            self.presenter_handler.handle_request(
                payload=payload, user_id=self.user_id,
            )
        self.assertEqual(
            context_manager.exception.message,
            f"Presenter non_existing_presenter does not exist.",
        )
