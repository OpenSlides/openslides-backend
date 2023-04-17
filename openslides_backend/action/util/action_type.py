from enum import Enum, auto


class ActionType(int, Enum):
    BACKEND_INTERNAL = auto()
    STACK_INTERNAL = auto()
    PUBLIC = auto()
