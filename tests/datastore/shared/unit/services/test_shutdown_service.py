from unittest.mock import MagicMock

import pytest

from openslides_backend.datastore.shared.di import injector
from openslides_backend.datastore.shared.services import ShutdownService
from tests.datastore import reset_di  # noqa


@pytest.fixture()
def shutdown_service(reset_di):  # noqa
    injector.register(ShutdownService, ShutdownService)
    yield injector.get(ShutdownService)


def test_shutdown_service_creation(shutdown_service):
    assert bool(shutdown_service)


def test_shutdown_service_registration(shutdown_service):
    service = MagicMock()

    shutdown_service.register(service)

    assert service in shutdown_service.instances


def test_shutdown_service_shutdown_multiple_services(shutdown_service):
    shutdown_service.instances = ["first_service", "second_service"]
    shutdown_service.shutdown_instance = si = MagicMock()

    shutdown_service.shutdown()

    assert si.call_count == 2
    assert si.call_args_list[0].args[0] == "first_service"
    assert si.call_args_list[1].args[0] == "second_service"


def test_shutdown_service_shutdown_single_service(shutdown_service):
    service = MagicMock()
    service.shutdown = MagicMock()
    shutdown_service.call_shutdown_handler = chs = MagicMock()

    shutdown_service.shutdown_instance(service)

    assert chs.call_count == 1


def test_shutdown_service_shutdown_single_service_no_handler(shutdown_service):
    service = None  # not callable
    shutdown_service.call_shutdown_handler = chs = MagicMock()

    shutdown_service.shutdown_instance(service)

    assert chs.call_count == 0


def test_shutdown_service_call_shutdown_handler(shutdown_service):
    service = MagicMock()
    service.shutdown = s = MagicMock()

    shutdown_service.shutdown_instance(service)

    s.assert_called_once()


def test_shutdown_service_call_shutdown_handler_with_error(shutdown_service):
    service = MagicMock()
    service.shutdown = s = MagicMock(side_effect=Exception())

    shutdown_service.shutdown_instance(service)

    s.assert_called_once()
