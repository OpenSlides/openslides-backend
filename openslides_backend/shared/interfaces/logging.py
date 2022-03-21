from typing import Protocol


class Logger(Protocol):  # pragma: no cover
    """
    Interface for logger object provided by LoggingModule.
    """

    def debug(self, message: str) -> None:
        ...

    def info(self, message: str) -> None:
        ...

    def warning(self, message: str) -> None:
        ...

    def error(self, message: str) -> None:
        ...

    def critical(self, message: str) -> None:
        ...

    def exception(self, message: Exception) -> None:
        ...


class LoggingModule(Protocol):  # pragma: no cover
    """
    Interface for module to provide a hierarchical logger.
    """

    def getLogger(self, name: str) -> Logger:
        ...
