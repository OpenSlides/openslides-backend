from typing import Protocol

import pytest

from openslides_backend.datastore.shared.di import (
    injector,
    service_as_factory,
    service_as_singleton,
    service_interface,
)
from openslides_backend.datastore.shared.di.exceptions import DependencyInjectionError


@service_interface
class ClientService(Protocol):
    pass


@service_interface
class MasterService(Protocol):
    pass


@service_as_singleton
class MasterServiceSingleton:
    pass


@service_as_factory
class MasterServiceFactory:
    pass


class BaseClientService:
    value: str

    def __init__(self):
        self.value = "default"


@service_as_singleton
class ClientServiceSingleton(BaseClientService):
    master_service: MasterService
    another_value: str

    def __init__(self, master_service: MasterService):
        self.init_master_service = master_service
        self.another_value = "default2"
        super().__init__()


@service_as_factory
class ClientServiceFactory(BaseClientService):
    master_service: MasterService
    another_value: str

    def __init__(self, master_service: MasterService):
        self.init_master_service = master_service
        self.another_value = "default2"
        super().__init__()


class TestWithProtocols:
    def test_singleton_and_factory(self):
        for client_service, master_service in (
            (ClientServiceFactory, MasterServiceFactory),
            (ClientServiceFactory, MasterServiceSingleton),
            (ClientServiceSingleton, MasterServiceSingleton),
        ):
            injector.register(MasterService, master_service)
            injector.register(ClientService, client_service)

            cs = injector.get(ClientService)

            assert type(cs) is client_service
            assert type(cs.master_service) is master_service
            assert cs.value == "default"
            assert cs.another_value == "default2"
            assert cs.init_master_service == cs.master_service

    def test_client_factory_service_factory_multi_get(self):
        injector.register(MasterService, MasterServiceFactory)
        injector.register(ClientService, ClientServiceFactory)

        a = injector.get(ClientService)
        b = injector.get(ClientService)

        assert a != b
        assert a.master_service != b.master_service

    def test_client_factory_service_singleton_multi_get(self):
        injector.register(MasterService, MasterServiceSingleton)
        injector.register(ClientService, ClientServiceFactory)

        a = injector.get(ClientService)
        b = injector.get(ClientService)

        assert a != b
        assert a.master_service == b.master_service

    def test_client_singleton_service_singleton_multi_get(self):
        injector.register(MasterService, MasterServiceSingleton)
        injector.register(ClientService, ClientServiceSingleton)

        a = injector.get(ClientService)
        b = injector.get(ClientService)

        assert a == b
        assert a.master_service == b.master_service

    def test_client_singleton_service_factory(self):
        injector.register(MasterService, MasterServiceFactory)

        with pytest.raises(DependencyInjectionError):
            injector.register(ClientService, ClientServiceSingleton)


@service_as_singleton
class ClientServiceSingletonDirectSingleton(BaseClientService):
    master_service: MasterServiceSingleton


@service_as_singleton
class ClientServiceSingletonDirectFactory(BaseClientService):
    master_service: MasterServiceFactory


class TestClientSingletonDirectInjection:
    def test_master_singleton(self):
        injector.register(MasterServiceSingleton, MasterServiceSingleton)
        injector.register(ClientService, ClientServiceSingletonDirectSingleton)

        a = injector.get(ClientService)
        b = injector.get(ClientService)

        assert a == b
        assert a.master_service == b.master_service

    def test_master_factory(self):
        injector.register(MasterServiceFactory, MasterServiceFactory)
        with pytest.raises(DependencyInjectionError):
            injector.register(ClientService, ClientServiceSingletonDirectFactory)


@service_as_factory
class ClientServiceFactoryDirectSingleton(BaseClientService):
    master_service: MasterServiceSingleton


@service_as_factory
class ClientServiceFactoryDirectFactory(BaseClientService):
    master_service: MasterServiceFactory


class TestClientFactoryDirectInjection:
    def test_master_singleton(self):
        injector.register(MasterServiceSingleton, MasterServiceSingleton)
        injector.register(ClientService, ClientServiceFactoryDirectSingleton)

        a = injector.get(ClientService)
        b = injector.get(ClientService)

        assert a != b
        assert a.master_service == b.master_service

    def test_master_factory(self):
        injector.register(MasterServiceFactory, MasterServiceFactory)
        injector.register(ClientService, ClientServiceFactoryDirectFactory)

        a = injector.get(ClientService)
        b = injector.get(ClientService)

        assert a != b
        assert a.master_service != b.master_service


def test_unknown_init_args():
    with pytest.raises(DependencyInjectionError):

        @service_as_factory
        class SomeService:
            def __init__(self, some_arg): ...


def test_check_implements_protocol_fail():
    class P(Protocol):
        def function(self) -> None: ...

    class C:
        pass

    with pytest.raises(DependencyInjectionError):
        injector.check_implements_protocol(P, C)
