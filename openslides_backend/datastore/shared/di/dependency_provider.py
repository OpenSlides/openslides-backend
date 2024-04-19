import inspect
from collections.abc import Callable
from textwrap import dedent
from typing import TypedDict

from .exceptions import DependencyInjectionError, DependencyNotFound

_DI_INFO = "__di_info__"


class DiInfo(TypedDict):
    type: str


_TYPE_SINGLETON = "singleton"
_TYPE_FACTORY = "factory"

# TODO: mock-save marker types (hasattr(MagicMock(), FACTORY_MARKER) is true......)


class DependencyProvider:
    def __init__(self):
        self.provider_map: dict[type, Callable] = {}

    def get(self, protocol):
        try:
            return self.provider_map[protocol]()
        except KeyError:
            raise DependencyNotFound(protocol)

    def register_as_singleton(self, protocol, cls):
        instance = cls()
        self.provider_map[protocol] = lambda: instance

    def register_as_factory(self, protocol, cls):
        self.provider_map[protocol] = cls

    def register(self, protocol, cls):
        self.check_implements_protocol(protocol, cls)
        if get_di_type(cls) == _TYPE_SINGLETON:
            self.register_as_singleton(protocol, cls)
        elif get_di_type(cls) == _TYPE_FACTORY:
            self.register_as_factory(protocol, cls)
        else:
            raise DependencyInjectionError(f"No marker found for {cls}")

    def check_implements_protocol(self, protocol, cls):
        protocol_funcs = self.get_functions_with_signatures(protocol)
        cls_funcs = self.get_functions_with_signatures(cls)
        for name, sig in protocol_funcs.items():
            if name not in cls_funcs or cls_funcs[name] != sig:
                raise DependencyInjectionError(
                    dedent(
                        f"""
                        Class {cls} does not implement function '{name}' of protocol\
                        {protocol} correctly.
                        Protocol implementation: {sig}
                        Class implementation: {cls_funcs.get(name)}
                        """
                    )
                )

    def get_functions_with_signatures(self, cls):
        # ignore all functions which start with an underscore
        return {
            t[0]: inspect.signature(t[1])
            for t in inspect.getmembers(cls)
            if t[0][0] != "_" and inspect.isfunction(t[1])
        }


injector = DependencyProvider()


def service_as_singleton(cls):
    set_type(cls, _TYPE_SINGLETON)
    return service(cls)


def service_as_factory(cls):
    set_type(cls, _TYPE_FACTORY)
    return service(cls)


def add_di_info(cls):
    if not has_di_info(cls):
        setattr(cls, _DI_INFO, {})


def get_di_type(cls) -> str | None:
    return getattr(cls, _DI_INFO, {}).get("type")


def has_di_info(cls):
    return hasattr(cls, _DI_INFO)


def set_type(cls, type):
    add_di_info(cls)
    getattr(cls, _DI_INFO)["type"] = type


def service(cls):
    annotations = cls.__dict__.get("__annotations__", {})
    service_mapping = {
        name: dep_cls for name, dep_cls in annotations.items() if has_di_info(dep_cls)
    }

    old_init = cls.__init__
    arg_names = inspect.getfullargspec(old_init)[0][1:]  # exclude "self"

    # Find protocols for the arguments
    arg_protocols = []
    # check, if all given arg names are services:
    for arg_name in arg_names:
        if arg_name not in service_mapping:
            raise DependencyInjectionError(
                f"Argument {arg_name} of {cls} is not an annotated "
                + "service of this class"
            )
        arg_protocols.append(service_mapping[arg_name])

    def new_init(self):
        all_resolved_services = {
            name: injector.get(protocol) for name, protocol in service_mapping.items()
        }

        # check for illegal factory-in-singleton injection

        injected_factories = [
            (name, service)
            for name, service in all_resolved_services.items()
            if get_di_type(service) == _TYPE_FACTORY
        ]
        if injected_factories and get_di_type(cls) == _TYPE_SINGLETON:
            raise DependencyInjectionError(
                f"Class {cls} is a singleton, but injected service "
                + f"{injected_factories[0][0]} "
                + f"({injected_factories[0][1]}) is a factory!"
            )

        for name, service in all_resolved_services.items():
            setattr(self, name, service)

        args_resolved_services = [
            service
            for name, service in all_resolved_services.items()
            if name in arg_names
        ]
        args_mapping = {x[0]: x[1] for x in zip(arg_names, args_resolved_services)}
        old_init(self, **args_mapping)

    cls.__init__ = new_init
    return cls


def service_interface(cls):
    add_di_info(cls)
    return cls
