from unittest.mock import MagicMock, patch

import pytest

from openslides_backend.datastore.shared.di import injector
from openslides_backend.datastore.shared.services import EnvironmentService
from openslides_backend.datastore.shared.util import BadCodingError
from openslides_backend.datastore.shared.util.logging import init_logging
from tests.datastore import reset_di  # noqa


@pytest.fixture()
def env_service(reset_di):  # noqa
    injector.register(EnvironmentService, EnvironmentService)
    yield injector.get(EnvironmentService)


def test_init_logging(env_service):
    reference_logger_name = MagicMock()
    flask_logger = MagicMock()
    with (
        patch("openslides_backend.datastore.shared.util.logging.logger") as logger,
        patch("openslides_backend.datastore.shared.util.logging.logging") as logging,
    ):
        logger.handlers = None
        reference_logger = MagicMock()
        logging.getLogger = MagicMock(return_value=reference_logger)
        init_logging(reference_logger_name, flask_logger)

        logger.setLevel.assert_called()
        logger.addHandler.assert_called()
        logging.getLogger.assert_called_with(reference_logger_name)
        assert logger.handlers == reference_logger.handlers
        assert flask_logger.handlers == reference_logger.handlers


def test_init_logging_error(env_service):
    with pytest.raises(BadCodingError):
        init_logging(MagicMock())
