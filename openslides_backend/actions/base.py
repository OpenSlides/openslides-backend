from typing import List, Optional

from ..utils.types import Event
from .types import Payload


class Action:
    def perform(self, payload: Payload, user_id: int) -> Event:
        """
        ...
        """
        self.user_id = user_id
        self.validate(payload)
        return self.create_event(payload)

    def validate(self, payload: Payload) -> None:
        """
        ...
        """
        raise NotImplementedError

    def create_event(self, payload: Payload, keys: Optional[List] = None) -> Event:
        """
        ...
        """
        raise NotImplementedError


class DatabaseAction(Action):
    def perform(self, payload: Payload, user_id: int) -> Event:
        """
        ...
        """
        self.user_id = user_id
        self.validate(payload)
        keys = self.read_database(payload)
        return self.create_event(payload, keys)

    def read_database(self, payload: Payload) -> List[str]:
        """
        ...
        """
        raise NotImplementedError  # TODO zweites Protocol
