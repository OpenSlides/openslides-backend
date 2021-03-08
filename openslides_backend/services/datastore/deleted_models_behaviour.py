from enum import Enum


class DeletedModelsBehaviour(int, Enum):
    NO_DELETED = 1
    ONLY_DELETED = 2
    ALL_MODELS = 3


class InstanceAdditionalBehaviour(int, Enum):
    ADDITIONAL_BEFORE_DBINST = 1
    DBINST_BEFORE_ADDITIONAL = 2
    ONLY_DBINST = 3
    ONLY_ADDITIONAL = 4
