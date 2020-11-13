from typing import Type
from unittest.mock import MagicMock, Mock

from openslides_backend.environment import get_environment
from openslides_backend.http.views import ActionView, PresenterView
from openslides_backend.services.media.interface import MediaService
from openslides_backend.services.permission.interface import PermissionService
from openslides_backend.shared.interfaces.wsgi import View, WSGIApplication
from openslides_backend.wsgi import OpenSlidesBackendServices, OpenSlidesBackendWSGI


def create_action_test_application() -> WSGIApplication:
    return create_test_application(ActionView)


def create_presenter_test_application() -> WSGIApplication:
    return create_test_application(PresenterView)


def create_test_application(view: Type[View]) -> WSGIApplication:
    environment = get_environment()
    services = OpenSlidesBackendServices(
        config={
            "permission_url": environment["permission_url"],
            "datastore_reader_url": environment["datastore_reader_url"],
            "datastore_writer_url": environment["datastore_writer_url"],
        },
        logging=MagicMock(),
    )
    mock_media_service = Mock(MediaService)
    services.media = MagicMock(return_value=mock_media_service)
    mock_permission_service = Mock(PermissionService)
    mock_permission_service.is_allowed = MagicMock(return_value=True)
    services.permission = MagicMock(return_value=mock_permission_service)

    # Create WSGI application instance. Inject logging module, view class and services container.
    application_factory = OpenSlidesBackendWSGI(
        logging=MagicMock(), view=view, services=services
    )
    application = application_factory.setup()

    return application
