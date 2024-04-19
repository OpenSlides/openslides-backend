from typing import Protocol
from unittest.mock import MagicMock

import pytest

from openslides_backend.datastore.shared.di import injector as default_injector
from openslides_backend.datastore.shared.di import (
    service_as_factory,
    service_as_singleton,
    service_interface,
)
from openslides_backend.datastore.shared.di.dependency_provider import (
    DependencyProvider,
)
from openslides_backend.datastore.shared.di.exceptions import (
    DependencyInjectionError,
    DependencyNotFound,
)
from tests.datastore import reset_di  # noqa


@pytest.fixture()
def injector():
    yield DependencyProvider()


@service_interface
class ServiceProtocol(Protocol):
    pass


class Service:
    pass


@service_as_singleton
class ServiceSingleton:
    pass


@service_as_factory
class ServiceFactory:
    pass


def test_default_injector():
    assert type(default_injector) is DependencyProvider


class TestRegistrationAsSingleton:
    def test_callable_provider(self, injector):
        injector.register_as_singleton(ServiceProtocol, Service)

        assert callable(injector.provider_map[ServiceProtocol])

    def test_returned_type_correct(self, injector):
        injector.register_as_singleton(ServiceProtocol, Service)

        assert type(injector.provider_map[ServiceProtocol]()) == Service

    def test_singleton(self, injector):
        injector.register_as_singleton(ServiceProtocol, Service)

        s1 = injector.provider_map[ServiceProtocol]()
        s2 = injector.provider_map[ServiceProtocol]()
        assert s1 == s2


class TestRegistrationAsFactory:
    def test_callable_provider(self, injector):
        injector.register_as_factory(ServiceProtocol, Service)

        assert callable(injector.provider_map[ServiceProtocol])

    def test_returned_type_correct(self, injector):
        injector.register_as_factory(ServiceProtocol, Service)

        assert type(injector.provider_map[ServiceProtocol]()) == Service

    def test_duplicate_instantiation(self, injector):
        injector.register_as_factory(ServiceProtocol, Service)

        s1 = injector.provider_map[ServiceProtocol]()
        s2 = injector.provider_map[ServiceProtocol]()
        assert s1 != s2


class TestRegistration:
    def test_no_marker(self, injector):
        with pytest.raises(DependencyInjectionError):
            injector.register(ServiceProtocol, Service)

    def test_singleton_marker(self, injector):
        injector.register_as_singleton = ras = MagicMock()
        injector.register_as_factory = raf = MagicMock()

        injector.register(ServiceProtocol, ServiceSingleton)

        assert ras.call_count == 1
        assert raf.call_count == 0

    def test_factory_marker(self, injector):
        injector.register_as_singleton = ras = MagicMock()
        injector.register_as_factory = raf = MagicMock()

        injector.register(ServiceProtocol, ServiceFactory)

        assert ras.call_count == 0
        assert raf.call_count == 1


class TestGet:
    def test_get(self, injector):
        instance = Service()
        injector.provider_map[ServiceProtocol] = lambda: instance

        assert injector.get(ServiceProtocol) == instance

    def test_get_unknown(self, injector):
        with pytest.raises(DependencyNotFound):
            injector.get(ServiceProtocol)


class TestWithoutProtocols:
    def test_callable_provider_as_factory(self, injector):
        injector.register_as_factory(Service, Service)

        assert callable(injector.provider_map[Service])

    def test_returned_type_correct_as_factory(self, injector):
        injector.register_as_factory(Service, Service)

        assert type(injector.provider_map[Service]()) == Service

    def test_callable_provider_as_singleton(self, injector):
        injector.register_as_singleton(Service, Service)

        assert callable(injector.provider_map[Service])

    def test_returned_type_correct_as_singleton(self, injector):
        injector.register_as_singleton(Service, Service)

        assert type(injector.provider_map[Service]()) == Service


class TestWithoutProtocolsAndMarkers:
    def test_callable_provider_as_factory(self, injector):
        injector.register(ServiceFactory, ServiceFactory)

        assert callable(injector.provider_map[ServiceFactory])

    def test_returned_type_correct_as_factory(self, injector):
        injector.register(ServiceFactory, ServiceFactory)

        assert type(injector.provider_map[ServiceFactory]()) == ServiceFactory

    def test_callable_provider_as_singleton(self, injector):
        injector.register(ServiceSingleton, ServiceSingleton)

        assert callable(injector.provider_map[ServiceSingleton])

    def test_returned_type_correct_as_singleton(self, injector):
        injector.register(ServiceSingleton, ServiceSingleton)

        assert type(injector.provider_map[ServiceSingleton]()) == ServiceSingleton
