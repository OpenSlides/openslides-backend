from typing import Any, Callable, Optional

from fastjsonschema import JsonSchemaException

from ..services.datastore.interface import Datastore
from ..shared.exceptions import PresenterException
from ..shared.interfaces import LoggingModule, Permission


class BasePresenter:
    """
    Base class for presenters.
    """

    data: Any
    permission: Permission
    database: Datastore
    logging: LoggingModule
    schema: Optional[Callable[[Any], None]] = None

    def __init__(
        self,
        data: Any,
        permission: Permission,
        datastore: Datastore,
        logging: LoggingModule,
    ):
        self.data = data
        self.permission = permission
        self.datastore = datastore
        self.logging = logging
        self.logger = logging.getLogger(__name__)

    def validate(self) -> None:
        """ Validates the given data. If schema is not set, assumes that no data should be given. """
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

    def get_result(self) -> Any:
        """ Does the actual work and returns the result depending on the data. """
        ...
