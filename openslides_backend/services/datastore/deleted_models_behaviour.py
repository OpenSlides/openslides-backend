from enum import Enum


class DeletedModelsBehaviour(int, Enum):
    NO_DELETED = 1
    ONLY_DELETED = 2
    ALL_MODELS = 3
