from typing import Callable, Type

from .action_set import ActionSet
from .actions_map import actions_map
from .base import Action


def register_action(
    name: str, internal: bool = False
) -> Callable[[Type[Action]], Type[Action]]:
    """
    Decorator to be used for action classes. Registers the class so that it can
    be found by the handler.
    """

    def wrapper(clazz: Type[Action]) -> Type[Action]:
        _register_action(name, clazz)
        clazz.internal = internal
        return clazz

    return wrapper


def register_action_set(
    name_prefix: str,
) -> Callable[[Type[ActionSet]], Type[ActionSet]]:
    """
    Decorator to be used for action set classes. Registers the class so that its
    actions can be found by the handler.
    """

    def wrapper(clazz: Type[ActionSet]) -> Type[ActionSet]:
        for route, action in clazz.get_actions().items():
            name = ".".join((name_prefix, route))
            _register_action(name, action)
        return clazz

    return wrapper


def _register_action(name: str, ActionClass: Type[Action]) -> Type[Action]:
    if actions_map.get(name):
        raise RuntimeError(f"Action {name} is registered twice.")
    actions_map[name] = ActionClass
    ActionClass.name = name
    return ActionClass
