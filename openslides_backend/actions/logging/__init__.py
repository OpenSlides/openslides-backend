import logging
from typing import Any

DEBUG = logging.DEBUG


def basicConfig(**kwargs: Any) -> None:
    logging.basicConfig(**kwargs)


def getLogger(name: str) -> logging.Logger:
    return logging.getLogger(name)
