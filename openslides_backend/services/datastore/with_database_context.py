from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar

from .adapter import DatastoreAdapter

T = TypeVar("T")
P = ParamSpec("P")


def with_database_context(method: Callable[P, T]) -> Callable[P, T]:
    @wraps(method)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        datastore = getattr(args[0], "datastore")
        assert isinstance(
            datastore, DatastoreAdapter
        ), "with_database_context can only decorate instance methods for classes with a datastore attribute"
        with datastore.get_database_context():
            return method(*args, **kwargs)

    return wrapper
