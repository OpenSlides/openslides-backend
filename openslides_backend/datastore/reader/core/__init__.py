from .reader import Reader
from .requests import (
    AggregateRequest,
    FilterRequest,
    GetAllRequest,
    GetEverythingRequest,
    GetManyRequest,
    GetManyRequestPart,
    GetRequest,
    HistoryInformationRequest,
    MinMaxRequest,
)


def setup_di():
    from openslides_backend.datastore.shared.di import injector

    from .reader_service import ReaderService

    injector.register(Reader, ReaderService)
