from enum import StrEnum


class EVENT_TYPE(StrEnum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    DELETE_FIELDS = "deletefields"
    LIST_FIELDS = "listfields"
    RESTORE = "restore"
