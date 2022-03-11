from typing import Protocol


class Env(Protocol):  # pragma: no cover
    """
    Interface for the object containing all environment variables and some
    helper methods.
    """

    def __getattr__(self, attr: str) -> str:
        ...

    def is_dev_mode(self) -> bool:
        ...

    def get_loglevel(self) -> str:
        ...
