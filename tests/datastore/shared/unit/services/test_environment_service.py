from tempfile import NamedTemporaryFile
from unittest.mock import MagicMock, patch

import pytest

from openslides_backend.datastore.shared.di import injector
from openslides_backend.datastore.shared.services import (
    EnvironmentService,
    EnvironmentVariableMissing,
)
from openslides_backend.datastore.shared.services.environment_service import (
    DATASTORE_DEV_MODE_ENVIRONMENT_VAR,
    DEV_SECRET,
)
from tests.datastore import reset_di  # noqa


@pytest.fixture()
def environment_service(reset_di):  # noqa
    injector.register(EnvironmentService, EnvironmentService)
    env_service = injector.get(EnvironmentService)
    yield env_service
    env_service.cache = {}


def test_environment_service_creation(environment_service):
    assert bool(environment_service)


def test_ensure_cache_not_in_cache(environment_service):
    key = MagicMock()
    environment_service.cache = {}
    with patch(
        "openslides_backend.datastore.shared.services.environment_service.os.environ.get"
    ) as get:
        get.return_value = v = MagicMock()

        environment_service.ensure_cache(key)

        assert environment_service.cache[key] == v
        get.assert_called_once()


def test_ensure_cache_found(environment_service):
    key = MagicMock()
    environment_service.cache = {key: "value"}
    with patch(
        "openslides_backend.datastore.shared.services.environment_service.os.environ.get"
    ) as get:
        environment_service.ensure_cache(key)

        assert get.call_count == 0


def test_try_get_in_cache(environment_service):
    key = MagicMock()
    value = MagicMock()
    environment_service.cache = {key: value}
    environment_service.ensure_cache = ec = MagicMock()

    assert environment_service.try_get(key) == value
    ec.assert_called_once()


def test_try_get_not_in_cache(environment_service):
    key = MagicMock()
    environment_service.cache = {}
    environment_service.ensure_cache = ec = MagicMock()

    assert environment_service.try_get(key) is None
    ec.assert_called_once()


def test_get_in_cache(environment_service):
    key = MagicMock()
    value = MagicMock()
    environment_service.cache = {key: value}
    environment_service.ensure_cache = ec = MagicMock()

    assert environment_service.get(key) == value
    ec.assert_called_once()


def test_get_not_in_cache(environment_service):
    key = MagicMock()
    environment_service.cache = {}
    environment_service.ensure_cache = ec = MagicMock()

    with pytest.raises(EnvironmentVariableMissing):
        environment_service.get(key)
    ec.assert_called_once()


def test_set(environment_service):
    key = MagicMock()
    value = MagicMock()

    environment_service.set(key, value)

    assert environment_service.cache[key] == value


def test_set_get(environment_service):
    key = MagicMock()
    value = MagicMock()

    environment_service.set(key, value)

    assert environment_service.get(key) == value


def test_is_dev_mode_not_set(environment_service):
    environment_service.cache = {DATASTORE_DEV_MODE_ENVIRONMENT_VAR: None}

    assert environment_service.is_dev_mode() is False


def test_is_dev_mode(environment_service):
    for value in ("1", "true", "True", "TRUE", "on", "On", "ON"):
        environment_service.cache = {DATASTORE_DEV_MODE_ENVIRONMENT_VAR: value}

        assert environment_service.is_dev_mode()


def test_get_from_file_dev_mode(environment_service):
    with patch(
        "openslides_backend.datastore.shared.services.environment_service.os.environ.get"
    ) as get:
        environment_service.cache = {DATASTORE_DEV_MODE_ENVIRONMENT_VAR: "1"}
        assert environment_service.get_from_file("TEST") == DEV_SECRET
        get.assert_not_called()


def test_get_from_file_non_dev(environment_service):
    with NamedTemporaryFile() as secret_file:
        secret_file.write(b"test")
        secret_file.seek(0)
        environment_service.cache = {
            "TEST_FILE": secret_file.name,
            DATASTORE_DEV_MODE_ENVIRONMENT_VAR: "0",
        }
        assert environment_service.get_from_file("TEST_FILE") == "test"


def test_get_from_file_not_existent(environment_service):
    environment_service.cache = {
        "TEST_FILE": "not_existent",
        DATASTORE_DEV_MODE_ENVIRONMENT_VAR: "0",
    }
    with pytest.raises(FileNotFoundError):
        environment_service.get_from_file("TEST_FILE")
