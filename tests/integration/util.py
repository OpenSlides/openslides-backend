from typing import Type
from unittest.mock import MagicMock

from openslides_backend.http.views import ActionView
from openslides_backend.shared.interfaces import View, WSGIApplication
from openslides_backend.wsgi import OpenSlidesBackendWSGI

from ..util import Client


def create_action_test_client() -> Client:
    return Client(create_action_test_application())


def create_action_test_application() -> WSGIApplication:
    return create_test_application(ActionView)


def create_test_application(view: Type[View]) -> WSGIApplication:
    application_factory = OpenSlidesBackendWSGI(
        logging=MagicMock(), view=view, services=MagicMock()
    )
    application = application_factory.setup()
    return application
