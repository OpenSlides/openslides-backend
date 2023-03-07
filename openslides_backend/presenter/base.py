from abc import abstractmethod
from typing import Any, Callable, Optional

from fastjsonschema import JsonSchemaException

from openslides_backend.shared.base_service_provider import BaseServiceProvider

from ..services.datastore.interface import DatastoreService
from ..shared.exceptions import PresenterException
from ..shared.interfaces.logging import LoggingModule
from ..shared.interfaces.services import Services


class BasePresenter(BaseServiceProvider):
    """
    Base class for presenters.
    """

    data: Any
    schema: Optional[Callable[[Any], None]] = None
    csrf_exempt: bool

    def __init__(
        self,
        data: Any,
        services: Services,
        datastore: DatastoreService,
        logging: LoggingModule,
        user_id: int,
    ):
        super().__init__(services, datastore, logging)
        self.data = data
        self.logger = logging.getLogger(__name__)
        self.user_id = user_id

    def validate(self) -> None:
        """Validates the given data. If schema is not set, assumes that no data should be given."""
        schema = type(self).schema
        if schema:
            if self.data is None:
                raise PresenterException("No data given.")
            try:
                schema(self.data)
            except JsonSchemaException as exception:
                raise PresenterException(exception.message)
        else:
            if self.data is not None:
                raise PresenterException("This presenter does not take data.")

    @abstractmethod
    def get_result(self) -> Any:
        """Does the actual work and returns the result depending on the data."""
        ...
