from functools import wraps
from typing import Any, Callable, Dict, Optional

from readerlib import DatabaseError
from readerlib import DatastoreException as ReaderDatastoreException
from readerlib import handle_internal_errors

from ...shared.exceptions import DatastoreException, DatastoreLockedException


def handle_datastore_errors(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args, **kwargs):  # type: ignore
        try:
            return func(*args, **kwargs)
        # the noqas are required because of a pyflakes bug: https://github.com/PyCQA/pyflakes/issues/643
        except (ReaderDatastoreException, DatabaseError) as e:  # noqa: F841

            def reraise() -> None:
                raise e  # noqa: F821

            error, _ = handle_internal_errors(reraise)()
            raise_datastore_error(error)

    return wrapper


def raise_datastore_error(
    error: Optional[Dict[str, Any]], error_message_prefix: str = ""
) -> None:
    error_message = error_message_prefix
    additional_error_message = error.get("error") if isinstance(error, dict) else None
    if additional_error_message is not None:
        type_verbose = additional_error_message.get("type_verbose")
        if type_verbose == "MODEL_LOCKED":
            broken_locks = (
                "'" + "', '".join(sorted(additional_error_message.get("keys"))) + "'"
            )
            raise DatastoreLockedException(
                " ".join(
                    (
                        error_message,
                        f"The following locks were broken: {broken_locks}",
                    )
                )
            )
        elif type_verbose == "MODEL_DOES_NOT_EXIST":
            error_message = " ".join(
                (
                    error_message,
                    f"Model '{additional_error_message.get('fqid')}' does not exist.",
                )
            )
        else:
            error_message = " ".join((error_message, str(additional_error_message)))
    raise DatastoreException(error_message)
