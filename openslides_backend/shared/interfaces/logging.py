from abc import abstractmethod
from typing import Protocol


class Logger(Protocol):
    """
    Interface for logger object provided by LoggingModule.
    """

    @abstractmethod
    def debug(self, message: str) -> None: ...

    @abstractmethod
    def info(self, message: str) -> None: ...

    @abstractmethod
    def warning(self, message: str) -> None: ...

    @abstractmethod
    def error(self, message: str) -> None: ...

    @abstractmethod
    def critical(self, message: str) -> None: ...

    @abstractmethod
    def exception(self, message: Exception) -> None: ...


class LoggingModule(Protocol):
    """
    Interface for module to provide a hierarchical logger.
    """

    @abstractmethod
    def getLogger(self, name: str) -> Logger: ...
