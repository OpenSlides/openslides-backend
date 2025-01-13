from enum import Enum


class EVENT_TYPE(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    DELETE_FIELDS = "deletefields"
    LIST_FIELDS = "listfields"
    RESTORE = "restore"
