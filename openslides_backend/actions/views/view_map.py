from typing import Callable, Dict, Type

from .base import View

view_map: Dict[str, Type[View]] = {}


def register_view(name: str) -> Callable[[Type[View]], Type[View]]:
    """
    Decorator to be used for view classes. Registers the class so that it can
    be found by the WSGI application.
    """

    def wrapper(view: Type[View]) -> Type[View]:
        view_map[name] = view
        return view

    return wrapper
