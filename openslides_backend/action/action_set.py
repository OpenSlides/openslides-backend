from typing import cast

from ..models.base import Model
from ..permissions.permissions import Permission
from .action import Action
from .generics.create import CreateAction
from .generics.delete import DeleteAction
from .generics.update import UpdateAction


class ActionSet:
    """
    Set of create, update and delete action for the given model.
    """

    model: Model
    permission: Permission | None = None

    create_schema: dict
    update_schema: dict
    delete_schema: dict

    CreateActionClass: type[Action] = CreateAction
    UpdateActionClass: type[Action] = UpdateAction
    DeleteActionClass: type[Action] = DeleteAction

    actions: dict[str, type[Action]]

    @classmethod
    def get_actions(cls) -> dict[str, type[Action]]:
        if not hasattr(cls, "actions"):
            actions = {}
            for route in ("create", "update", "delete"):
                schema = getattr(cls, route + "_schema")
                base_class = getattr(cls, route.capitalize() + "ActionClass")
                clazz = cast(
                    type[Action],
                    type(
                        type(cls.model).__name__ + route.capitalize(),
                        (base_class,),
                        dict(model=cls.model, schema=schema),
                    ),
                )
                actions[route] = clazz
            cls.actions = actions
        return cls.actions

    @classmethod
    def get_action(cls, route: str) -> type[Action]:
        return cls.get_actions()[route]
