from typing import Dict, Type

from ..models.base import Model
from .base import Action
from .generics import CreateAction, DeleteAction, UpdateAction


class ActionSet:
    """
    Set of create, update and delete action for the given model.
    """

    model: Model

    create_schema: Dict
    update_schema: Dict
    delete_schema: Dict

    routes = {"create": CreateAction, "update": UpdateAction, "delete": DeleteAction}

    actions: Dict[str, Type[Action]]

    @classmethod
    def get_actions(cls) -> Dict[str, Type[Action]]:
        if not hasattr(cls, "actions"):
            actions = {}
            for route, base_class in cls.routes.items():
                schema = getattr(cls, route + "_schema")
                clazz = type(
                    type(cls.model).__name__ + route.capitalize(),
                    (base_class,),
                    dict(model=cls.model, schema=schema),
                )
                actions[route] = clazz
            cls.actions = actions
        return cls.actions

    @classmethod
    def get_action(cls, route: str) -> Type[Action]:
        return cls.get_actions()[route]
