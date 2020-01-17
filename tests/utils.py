from unittest.mock import MagicMock

from dependency_injector import containers, providers  # type: ignore
from werkzeug.test import Client as WerkzeugClient
from werkzeug.wrappers import BaseResponse

from openslides_backend.main import Application, OpenSlidesBackend
from openslides_backend.shared.patterns import Collection, FullQualifiedField

from .fake_services.authentication import AuthenticationTestAdapter
from .fake_services.database import DatabaseTestAdapter
from .fake_services.event_store import EventStoreTestAdapter
from .fake_services.permission import PermissionTestAdapter


class ResponseWrapper(BaseResponse):
    pass


class Client(WerkzeugClient):
    pass


class FakeServices(containers.DeclarativeContainer):
    config = providers.Configuration("config")
    authentication = providers.Singleton(AuthenticationTestAdapter, config.user_id)
    permission = providers.Singleton(PermissionTestAdapter)
    database = providers.Singleton(DatabaseTestAdapter)
    event_store = providers.Singleton(EventStoreTestAdapter)


def create_test_application(user_id: int) -> Application:
    """
    Application factory function to create a new instance of the application.

    Uses test (fake) services.
    """

    # Setup services
    services = FakeServices(config={"user_id": user_id})

    # Create application instance. Inject services.
    application_factory = OpenSlidesBackend(logging=MagicMock(), services=services)
    application = application_factory.setup()
    return application


def get_fqfield(key: str) -> FullQualifiedField:
    collection, id, field = key.split("/")
    return FullQualifiedField(Collection(collection), int(id), field)
