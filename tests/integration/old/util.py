from typing import Any, Dict, Type
from unittest.mock import MagicMock

from dependency_injector import containers, providers

from openslides_backend.http.views import ActionView, PresenterView
from openslides_backend.services.datastore.adapter import DatastoreAdapter
from openslides_backend.shared.interfaces import View, WSGIApplication
from openslides_backend.shared.patterns import FullQualifiedField
from openslides_backend.wsgi import OpenSlidesBackendWSGI

from .fake_services.authentication import AuthenticationTestAdapter
from .fake_services.datastore import DatastoreTestAdapter
from .fake_services.http_engine import HTTPTestEngine
from .fake_services.permission import PermissionTestAdapter


class FakeServices(containers.DeclarativeContainer):
    config = providers.Configuration("config")
    logging = providers.Object(0)
    authentication = providers.Singleton(AuthenticationTestAdapter, config.user_id)
    superuser = providers.Configuration("superuser")
    datastore_content = providers.Configuration("datastore_content")
    expected_write_data = providers.Configuration("expected_write_data")
    permission = providers.Singleton(PermissionTestAdapter, superuser)
    engine = providers.Singleton(HTTPTestEngine, datastore_content, expected_write_data)
    datastore = providers.Factory(DatastoreAdapter, engine, logging)


def create_test_application_with_fake(
    user_id: int,
    view_name: str,
    superuser: int,
    datastore_content: Dict[FullQualifiedField, Any],
    expected_write_data: str,
) -> WSGIApplication:
    """
    Application factory function to create a new instance of the application.
    Uses test (fake) services.
    """
    # Get view class
    view: Type[View]
    if view_name == "ActionView":
        view = ActionView
    elif view_name == "PresenterView":
        view = PresenterView
    else:
        raise

    # Setup services
    services = FakeServices(
        config={"user_id": user_id},
        logging=MagicMock(),
        superuser=superuser,
        datastore_content=datastore_content,
        expected_write_data=expected_write_data,
    )

    # Create application instance. Inject services.
    application_factory = OpenSlidesBackendWSGI(
        logging=MagicMock(), view=view, services=services
    )
    application = application_factory.setup()

    return application


class FakeServicesOld(containers.DeclarativeContainer):
    config = providers.Configuration("config")
    authentication = providers.Singleton(AuthenticationTestAdapter, config.user_id)
    superuser = providers.Configuration("superuser")
    permission = providers.Singleton(PermissionTestAdapter, superuser)
    datastore = providers.Singleton(DatastoreTestAdapter, old_style_testing=True)


def create_test_application_old(
    user_id: int,
    view_name: str,
    superuser: int,
) -> WSGIApplication:
    """
    Application factory function to create a new instance of the application.
    Uses test (fake) services.
    """
    # Get view class
    view: Type[View]
    if view_name == "ActionView":
        view = ActionView
    elif view_name == "PresenterView":
        view = PresenterView
    else:
        raise

    # Setup services
    services = FakeServicesOld(config={"user_id": user_id}, superuser=superuser)

    # Create application instance. Inject services.
    application_factory = OpenSlidesBackendWSGI(
        logging=MagicMock(), view=view, services=services
    )
    application = application_factory.setup()
    return application
