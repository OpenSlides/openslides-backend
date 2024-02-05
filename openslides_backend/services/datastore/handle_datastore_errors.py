from collections.abc import Callable, Iterable
from functools import wraps
from typing import Any, cast

from datastore.shared.flask_frontend import handle_internal_errors
from datastore.shared.postgresql_backend import DatabaseError
from datastore.shared.util import DatastoreException as ReaderDatastoreException

from ...shared.exceptions import DatastoreException, DatastoreLockedException
from ...shared.interfaces.env import Env
from ...shared.interfaces.logging import Logger


def handle_datastore_errors(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(self, *args, **kwargs):  # type: ignore
        try:
            return func(self, *args, **kwargs)
        # the noqas are required because of a pyflakes bug: https://github.com/PyCQA/pyflakes/issues/643
        except (ReaderDatastoreException, DatabaseError) as e:  # noqa: F841

            def reraise() -> None:
                raise e  # noqa: F821

            error, _ = handle_internal_errors(reraise)()
            raise_datastore_error(error, logger=self.logger, env=self.env)

    return wrapper


def raise_datastore_error(
    error: dict[str, Any] | None,
    error_message_prefix: str = "",
    logger: Logger | None = None,
    env: Env | None = None,
) -> None:
    error_message = error_message_prefix
    type_verbose: str = ""
    additional_error_message = error.get("error") if isinstance(error, dict) else None
    if additional_error_message is not None:
        if isinstance(additional_error_message, dict):
            type_verbose = additional_error_message.get("type_verbose", "")
            if type_verbose == "MODEL_LOCKED":
                broken_locks = (
                    "'"
                    + "', '".join(
                        sorted(
                            cast(Iterable[str], additional_error_message.get("keys"))
                        )
                    )
                    + "'"
                )
                error_message = " ".join(
                    (
                        error_message,
                        f"The following locks were broken: {broken_locks}",
                    )
                )
                if logger:
                    logger.debug(error_message)
                if env and not env.is_dev_mode():
                    error_message = "Datastore Error"
                raise DatastoreLockedException(error_message)
            elif type_verbose == "MODEL_DOES_NOT_EXIST":
                error_message = " ".join(
                    (
                        error_message,
                        f"Model '{additional_error_message.get('fqid')}' does not exist.",
                    )
                )
            else:
                error_message = " ".join((error_message, str(additional_error_message)))
        else:
            error_message = " ".join((error_message, str(additional_error_message)))
    if logger:
        logger.debug(error_message)
    if env and not env.is_dev_mode():
        error_message = "Datastore Error"
    raise DatastoreException(error_message)
