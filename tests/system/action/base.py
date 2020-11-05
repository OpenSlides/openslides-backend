from openslides_backend.shared.interfaces.wsgi import WSGIApplication
from tests.system.base import BaseSystemTestCase
from tests.system.util import create_action_test_application


class BaseActionTestCase(BaseSystemTestCase):
    def get_application(self) -> WSGIApplication:
        return create_action_test_application()
