import logging
import sys

from openslides_backend.datastore.shared.di import injector
from openslides_backend.datastore.shared.services import EnvironmentService
from openslides_backend.datastore.shared.util import BadCodingError

logger = logging.getLogger("datastore")


def init_logging(reference_logger_name=None, flask_logger=None):
    env_service = injector.get(EnvironmentService)
    level = env_service.try_get("DATASTORE_LOG_LEVEL")
    if not level:
        level = "DEBUG" if env_service.is_dev_mode() else "INFO"
    logger.setLevel(level)

    if not logger.handlers:
        formatter = logging.Formatter(
            fmt="%(asctime)s.%(msecs)03d: [%(pathname)s] [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
        handler = logging.StreamHandler(sys.stdout)
        handler.flush = sys.stdout.flush  # type: ignore
        handler.setLevel(level)
        handler.setFormatter(formatter)

        logger.addHandler(handler)

    if reference_logger_name:
        if not flask_logger:
            raise BadCodingError(
                "You have to give a flask logger to overwrite with a reference logger!"
            )
        # Overwrite all important handlers to redirect all output where we want it
        for curr_logger in (logger, flask_logger, logging.getLogger("werkzeug")):
            reference_logger = logging.getLogger(reference_logger_name)
            curr_logger.handlers = reference_logger.handlers
