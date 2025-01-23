from collections.abc import Callable
from typing import Protocol

PrintFunction = Callable[..., None]


class MigrationLogger(Protocol):
    def set_verbose(self, verbose: bool) -> None:
        """
        Set if verbose message should be logged.
        """

    def set_print_fn(self, print_fn: PrintFunction) -> None:
        """
        Sets the print function to be used for logging.
        """

    def info(self, message: str) -> None:
        """
        Logs the message.
        """

    def debug(self, message: str) -> None:
        """
        Logs the message if verbose is true.
        """


class MigrationLoggerImplementation:
    def __init__(self) -> None:
        self.verbose: bool = False
        self.print_fn = print

    def set_verbose(self, verbose: bool) -> None:
        self.verbose = verbose

    def set_print_fn(self, print_fn: PrintFunction) -> None:
        self.print_fn = print_fn

    def info(self, message: str) -> None:
        self.print_fn(message)

    def debug(self, message: str) -> None:
        if self.verbose:
            self.print_fn(message)
