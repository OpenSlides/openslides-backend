from typing import Iterable

from ..adapters.protocols import DatabaseAdapter, Event, PermissionAdapter
from ..general.exception import BackendBaseException
from .types import DataSet, Payload


class ActionException(BackendBaseException):
    pass


class PermissionDenied(BackendBaseException):
    pass


class Action:
    """
    Base class for actions.
    """

    position = 0

    def __init__(
        self, permission_adapter: PermissionAdapter, database_adapter: DatabaseAdapter
    ) -> None:
        self.permission_adapter = permission_adapter
        self.database_adapter = database_adapter

    def perform(self, payload: Payload, user_id: int) -> Iterable[Event]:
        """
        Entrypoint to perform the action.
        """
        self.user_id = user_id
        self.check_permission_on_entry()
        self.validate(payload)
        dataset = self.prepare_dataset(payload)
        self.check_permission_on_dataset(dataset)
        return self.create_events(dataset)

    def check_permission_on_entry(self) -> None:
        """
        Checks permission at the beginning of the action.
        """
        raise NotImplementedError

    def validate(self, payload: Payload) -> None:
        """
        Validates payload. Raises ActionException if payload is invalid.
        """
        raise NotImplementedError

    def prepare_dataset(self, payload: Payload) -> DataSet:
        """
        Prepares dataset from payload. Also fires all necessary database
        queries.
        """
        raise NotImplementedError

    def check_permission_on_dataset(self, dataset: DataSet) -> None:
        """
        Checks permission in the middle of the action according to dataset. Can
        be used for extra checks. Just passes at default.
        """
        pass

    def create_events(self, dataset: DataSet) -> Iterable[Event]:
        """
        Takes dataset and creates events that can be sent to event store.
        """
        raise NotImplementedError

    def set_min_position(self, position: int) -> None:
        """
        Sets self.position to the new value position if this value is smaller
        than the old one. Sets it if it is the first call.
        """
        if self.position == 0:
            self.position = position
        else:
            self.position = min(position, self.position)
