from .db_events import (
    BaseDbEvent,
    DbCreateEvent,
    DbDeleteEvent,
    DbDeleteFieldsEvent,
    DbListUpdateEvent,
    DbRestoreEvent,
    DbUpdateEvent,
    apply_event_to_models,
)
from .event_translator import EventTranslator
from .sql_database_backend_service import SqlDatabaseBackendService


def setup_di():
    from openslides_backend.datastore.shared.di import injector

    from .event_translator import EventTranslatorService

    injector.register(EventTranslator, EventTranslatorService)
