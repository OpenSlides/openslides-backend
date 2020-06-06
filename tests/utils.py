from typing import Type
from unittest.mock import MagicMock

from dependency_injector import containers, providers  # type: ignore
from werkzeug.test import Client as WerkzeugClient
from werkzeug.wrappers import BaseResponse

from openslides_backend.http.views import ActionsView, PresenterView
from openslides_backend.shared.interfaces import View, WSGIApplication
from openslides_backend.shared.patterns import (
    KEYSEPARATOR,
    Collection,
    FullQualifiedField,
    FullQualifiedId,
)
from openslides_backend.wsgi import OpenSlidesBackendWSGI

from .fake_services.authentication import AuthenticationTestAdapter
from .fake_services.database import DatabaseTestAdapter
from .fake_services.permission import PermissionTestAdapter


class ResponseWrapper(BaseResponse):
    pass


class Client(WerkzeugClient):
    pass


class FakeServices(containers.DeclarativeContainer):
    config = providers.Configuration("config")
    authentication = providers.Singleton(AuthenticationTestAdapter, config.user_id)
    permission = providers.Singleton(PermissionTestAdapter)
    datastore = providers.Singleton(DatabaseTestAdapter)


def create_test_application(user_id: int, view_name: str) -> WSGIApplication:
    """
    Application factory function to create a new instance of the application.

    Uses test (fake) services.
    """
    # Get view class
    view: Type[View]
    if view_name == "ActionsView":
        view = ActionsView
    elif view_name == "PresenterView":
        view = PresenterView
    else:
        raise

    # Setup services
    services = FakeServices(config={"user_id": user_id})

    # Create application instance. Inject services.
    application_factory = OpenSlidesBackendWSGI(
        logging=MagicMock(), view=view, services=services
    )
    application = application_factory.setup()
    return application


def get_fqid(value: str) -> FullQualifiedId:
    """
    Returns a FullQualifiedId parsed from the given value.
    """
    collection, id = value.split(KEYSEPARATOR)
    return FullQualifiedId(Collection(collection), int(id))


def get_fqfield(value: str) -> FullQualifiedField:
    """
    Returns a FullQualifiedField parsed from the given value.
    """
    collection, id, field = value.split(KEYSEPARATOR)
    return FullQualifiedField(Collection(collection), int(id), field)
