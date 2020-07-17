from typing import Callable, Iterable, Tuple, Type

from ..models.base import Model
from .action_interface import ActionPayload
from .base import Action
from .generics import CreateAction, DeleteAction, UpdateAction


class ActionSet:
    """
    Set of create, update and delete action for the given model.
    """

    model: Model

    create_schema: Callable[[ActionPayload], None]
    update_schema: Callable[[ActionPayload], None]
    delete_schema: Callable[[ActionPayload], None]

    routes = {"create": CreateAction, "update": UpdateAction, "delete": DeleteAction}

    @classmethod
    def get_actions(cls) -> Iterable[Tuple[str, Type[Action]]]:
        for route, base_class in cls.routes.items():
            schema = getattr(cls, route + "_schema")
            clazz = type(
                type(cls.model).__name__ + route.capitalize(),
                (base_class,),
                dict(model=cls.model, schema=schema),
            )
            yield route, clazz
