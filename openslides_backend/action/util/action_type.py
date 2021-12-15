from enum import Enum, auto


class ActionType(Enum):
    BACKEND_INTERNAL = auto()
    STACK_INTERNAL = auto()
    PUBLIC = auto()
