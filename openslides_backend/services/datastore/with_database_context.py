from functools import wraps
from typing import Callable

from .adapter import DatastoreAdapter


def with_database_context(method: Callable) -> Callable:
    @wraps(method)
    def wrapper(self, *args, **kwargs):  # type: ignore
        assert hasattr(self, "datastore") and isinstance(
            self.datastore, DatastoreAdapter
        ), "with_database_context can only decorate instance methods for classes with a datastore attribute"
        with self.datastore.get_database_context():
            return method(self, *args, **kwargs)

    return wrapper
