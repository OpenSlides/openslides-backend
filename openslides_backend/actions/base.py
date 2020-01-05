from typing import Iterable

from ..services.providers import DatabaseProvider
from ..utils.types import Event
from .types import DataSet, Payload


class Action:
    """
    Base class for actions.
    """

    position = 0

    def __init__(self, database_adapter: DatabaseProvider) -> None:
        self.database_adapter = database_adapter

    def perform(self, payload: Payload, user_id: int) -> Iterable[Event]:
        """
        Entrypoint to perform the action.
        """
        self.user_id = user_id
        self.validate(payload)
        dataset = self.prepare_dataset(payload)
        return self.create_events(dataset)

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
