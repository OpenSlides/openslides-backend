from typing import Callable, Dict, Type

from .base import Action

action_map: Dict[str, Type[Action]] = {}


def register_action(name: str) -> Callable[[Type[Action]], Type[Action]]:
    """
    Decorator to be used for action classes. Registers the class so that it can
    be found by the view.
    """

    def wrapper(action: Type[Action]) -> Type[Action]:
        action_map[name] = action
        return action

    return wrapper
