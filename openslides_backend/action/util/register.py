from typing import Callable, Type

from ..action import Action
from ..action_set import ActionSet
from .action_type import ActionType
from .actions_map import actions_map


def register_action(
    name: str, action_type: ActionType = ActionType.PUBLIC
) -> Callable[[Type[Action]], Type[Action]]:
    """
    Decorator to be used for action classes. Registers the class so that it can
    be found by the handler.
    """

    def wrapper(clazz: Type[Action]) -> Type[Action]:
        _register_action(name, clazz)
        clazz.action_type = action_type
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
            action.permission = clazz.permission
            _register_action(name, action)
        return clazz

    return wrapper


def _register_action(name: str, ActionClass: Type[Action]) -> Type[Action]:
    if actions_map.get(name):
        raise RuntimeError(f"Action {name} is registered twice.")
    actions_map[name] = ActionClass
    ActionClass.name = name
    return ActionClass
