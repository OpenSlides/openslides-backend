from typing import Any, Dict, Optional, Callable
from ..shared.exceptions import PresenterException

from ..services.datastore.interface import Datastore
from ..shared.interfaces import Permission, LoggingModule
from fastjsonschema import JsonSchemaException


class BasePresenter:
    """
    Base class for presenters.
    """

    data: Optional[Any]
    permission: Permission
    database: Datastore
    logging: LoggingModule

    def __init__(self, data: Optional[Any], permission: Permission, datastore: Datastore, logging: LoggingModule):
        self.data = data
        self.permission = permission
        self.datastore = datastore
        self.logging = logging
        self.logger = logging.getLogger(__name__)
    
    def validate(self) -> None:
        """ Validates the given data. If self.schema is not set, assumes that no data should be given. """
        if self.schema:
            if self.data is None:
                raise PresenterException("No data given.")
            try:
                # unfortunately, python injects self if we use the bounded method, so
                # we have to use the class method
                self.__class__.schema(self.data)
            except JsonSchemaException as exception:
                raise PresenterException(exception.message)
        else:
            if self.data is not None:
                raise PresenterException("This presenter does not take data.")

    def get_result(self) -> Any:
        """ Does the actual work and returns the result depending on the data. """
        ...
