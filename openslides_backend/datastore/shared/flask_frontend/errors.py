from textwrap import dedent

from werkzeug.exceptions import default_exceptions

from openslides_backend.datastore.shared.di import injector
from openslides_backend.datastore.shared.postgresql_backend.connection_handler import (
    DatabaseError,
)
from openslides_backend.datastore.shared.services import EnvironmentService
from openslides_backend.datastore.shared.util import (
    DatastoreNotEmpty,
    InvalidDatastoreState,
    InvalidFormat,
    ModelDoesNotExist,
    ModelExists,
    ModelLocked,
    ModelNotDeleted,
    logger,
)

# internal errors


class ERROR_CODES:
    INVALID_FORMAT = 1
    INVALID_REQUEST = 2
    MODEL_DOES_NOT_EXIST = 3
    MODEL_EXISTS = 4
    MODEL_NOT_DELETED = 5
    MODEL_LOCKED = 6
    INVALID_DATASTORE_STATE = 7
    DATASTORE_NOT_EMPTY = 8


def handle_internal_errors(fn):
    def wrapper(*args, **kwargs):
        error_dict = None
        try:
            return fn(*args, **kwargs)
        except DatabaseError as e:
            return {"error": e.msg}, 500
        except InvalidFormat as e:
            error_dict = {
                "type": ERROR_CODES.INVALID_FORMAT,
                "msg": e.msg,
                "type_verbose": "INVALID_FORMAT",
            }
        except InvalidRequest as e:
            error_dict = {
                "type": ERROR_CODES.INVALID_REQUEST,
                "msg": e.msg,
                "type_verbose": "INVALID_REQUEST",
            }
        except ModelDoesNotExist as e:
            error_dict = {
                "type": ERROR_CODES.MODEL_DOES_NOT_EXIST,
                "fqid": e.fqid,
                "type_verbose": "MODEL_DOES_NOT_EXIST",
            }
        except ModelExists as e:
            error_dict = {
                "type": ERROR_CODES.MODEL_EXISTS,
                "fqid": e.fqid,
                "type_verbose": "MODEL_EXISTS",
            }
        except ModelNotDeleted as e:
            error_dict = {
                "type": ERROR_CODES.MODEL_NOT_DELETED,
                "fqid": e.fqid,
                "type_verbose": "MODEL_NOT_DELETED",
            }
        except ModelLocked as e:
            error_dict = {
                "type": ERROR_CODES.MODEL_LOCKED,
                "keys": e.keys,
                "type_verbose": "MODEL_LOCKED",
            }
        except InvalidDatastoreState as e:
            error_dict = {
                "type": ERROR_CODES.INVALID_DATASTORE_STATE,
                "msg": e.msg,
                "type_verbose": "INVALID_DATASTORE_STATE",
            }
        except DatastoreNotEmpty as e:
            error_dict = {
                "type": ERROR_CODES.DATASTORE_NOT_EMPTY,
                "msg": e.msg,
                "type_verbose": "DATASTORE_NOT_EMPTY",
            }
        except Exception as e:
            print(e, type(e))
            raise e

        env_service = injector.get(EnvironmentService)
        if env_service.is_dev_mode():
            logger.debug(f"HTTP error 400: {error_dict}")

        return {"error": error_dict}, 400

    return wrapper


# http errors


class InvalidRequest(Exception):
    def __init__(self, msg):
        self.msg = msg


def handle_http_error(ex):
    return (
        dedent(
            f"""\
        <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
        <title>{ex.code} {ex.name}</title>
        <h1>{ex.name}</h1>
        <p><img src="https://http.cat/{ex.code}"></img></p>
        """
        ),
        ex.code,
    )


def register_error_handlers(app):
    # register for all error status codes
    for code in default_exceptions.keys():
        app.register_error_handler(code, handle_http_error)
