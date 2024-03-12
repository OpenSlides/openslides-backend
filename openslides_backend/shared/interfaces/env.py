from abc import abstractmethod
from typing import Protocol


class Env(Protocol):
    """
    Interface for the object containing all environment variables and some
    helper methods.
    """

    @abstractmethod
    def __getattr__(self, attr: str) -> str: ...

    @abstractmethod
    def is_dev_mode(self) -> bool: ...

    @abstractmethod
    def is_otel_enabled(self) -> bool: ...

    @abstractmethod
    def get_loglevel(self) -> str: ...
