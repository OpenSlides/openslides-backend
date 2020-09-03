from typing import Type
from unittest.mock import MagicMock

from openslides_backend.environment import get_environment
from openslides_backend.http.views import ActionView, PresenterView
from openslides_backend.shared.interfaces import View, WSGIApplication
from openslides_backend.wsgi import OpenSlidesBackendServices, OpenSlidesBackendWSGI

from ..util import Client


def create_action_test_client() -> Client:
    return Client(create_action_test_application())


def create_presenter_test_client() -> Client:
    return Client(create_presenter_test_application())


def create_action_test_application() -> WSGIApplication:
    return create_test_application(ActionView)


def create_presenter_test_application() -> WSGIApplication:
    return create_test_application(PresenterView)


def create_test_application(view: Type[View]) -> WSGIApplication:
    environment = get_environment()
    services = OpenSlidesBackendServices(
        config={
            "authentication_url": environment["authentication_url"],
            "permission_url": environment["permission_url"],
            "datastore_reader_url": environment["datastore_reader_url"],
            "datastore_writer_url": environment["datastore_writer_url"],
        },
        logging=MagicMock(),
    )

    # Create WSGI application instance. Inject logging module, view class and services container.
    application_factory = OpenSlidesBackendWSGI(
        logging=MagicMock(), view=view, services=services
    )
    application = application_factory.setup()

    return application
