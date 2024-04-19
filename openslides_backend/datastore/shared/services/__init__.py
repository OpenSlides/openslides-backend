from openslides_backend.datastore.shared.di.dependency_provider import (
    service_as_singleton,
)
from openslides_backend.shared.env import Environment
from openslides_backend.shared.interfaces.env import Env

from .environment_service import EnvironmentService, EnvironmentVariableMissing
from .read_database import HistoryInformation, ReadDatabase
from .shutdown_service import ShutdownService


def setup_di():
    from openslides_backend.datastore.shared.di import injector

    injector.register(EnvironmentService, EnvironmentService)
    injector.register(ShutdownService, ShutdownService)
