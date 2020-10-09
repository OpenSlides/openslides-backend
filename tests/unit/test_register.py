from unittest import TestCase
from unittest.mock import MagicMock

from openslides_backend.action.register import _register_action


class ActionRegisterTest(TestCase):
    def test_double_register(self) -> None:
        _register_action("test_dummy_action", MagicMock)
        with self.assertRaises(RuntimeError):
            _register_action("test_dummy_action", MagicMock)
