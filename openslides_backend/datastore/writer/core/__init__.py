from .database import Database
from .write_request import (
    BaseRequestEvent,
    CollectionFieldLock,
    CollectionFieldLockWithFilter,
    RequestCreateEvent,
    RequestDeleteEvent,
    RequestRestoreEvent,
    RequestUpdateEvent,
    WriteRequest,
)
from .writer import Writer


def setup_di():
    from openslides_backend.datastore.shared.di import injector

    from .writer_service import WriterService

    injector.register(Writer, WriterService)
