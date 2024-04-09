import json
from typing import Any

from openslides_backend.datastore.shared.postgresql_backend import (
    EVENT_TYPE,
    ListUpdatesDict,
)
from openslides_backend.datastore.shared.typing import Field, Fqid, Model
from openslides_backend.datastore.shared.util import (
    InvalidKeyFormat,
    assert_is_field,
    assert_is_fqid,
    is_reserved_field,
)


class BadEventException(Exception):
    pass


def assert_no_special_field(field: Any) -> None:
    if is_reserved_field(field):
        raise BadEventException(f"Field {field} is reserved")


class BaseEvent:
    type: EVENT_TYPE
    fqid: Fqid
    data: Any

    def __init__(self, fqid: Fqid, data: Any) -> None:
        self.fqid = fqid
        self.data = data
        try:
            self.check()
        except InvalidKeyFormat as e:
            raise BadEventException(e.msg)

    def check(self) -> None:
        assert_is_fqid(self.fqid)

    def get_data(self) -> Any:
        return self.data

    def clone(self) -> "BaseEvent":
        data_copy = json.loads(json.dumps(self.get_data()))
        return self.__class__(self.fqid, data_copy)


class _ModelEvent(BaseEvent):
    data: Model

    def __init__(self, fqid: Fqid, data: Model) -> None:
        super().__init__(fqid, data)

    def check(self) -> None:
        super().check()
        for field, value in self.data.items():
            assert_is_field(field)
            assert_no_special_field(field)
            if value is None:
                raise BadEventException(f"The value of {field} must not be None")


class CreateEvent(_ModelEvent):
    type = EVENT_TYPE.CREATE


class UpdateEvent(_ModelEvent):
    type = EVENT_TYPE.UPDATE


class DeleteFieldsEvent(BaseEvent):
    type = EVENT_TYPE.DELETE_FIELDS

    data: list[Field]

    def __init__(self, fqid: Fqid, data: list[Field]) -> None:
        super().__init__(fqid, data)

    def check(self) -> None:
        super().check()
        for field in self.data:
            assert_is_field(field)
            assert_no_special_field(field)


class ListUpdateEvent(BaseEvent):
    type = EVENT_TYPE.LIST_FIELDS

    add: ListUpdatesDict
    remove: ListUpdatesDict

    def __init__(self, fqid: Fqid, data: dict[str, ListUpdatesDict]) -> None:
        self.add = data.pop("add", {})
        self.remove = data.pop("remove", {})
        super().__init__(fqid, data)

    def check(self) -> None:
        if self.data:
            raise BadEventException("Only add and remove is allowed")

        all_fields = set(self.add.keys()).union(set(self.remove.keys()))
        for field in all_fields:
            assert_is_field(field)
            assert_no_special_field(field)

    def get_data(self) -> Any:
        return {"add": self.add, "remove": self.remove}


class DeleteEvent(BaseEvent):
    type = EVENT_TYPE.DELETE

    def __init__(self, fqid: Fqid, data: Any = None) -> None:
        super().__init__(fqid, None)


class RestoreEvent(BaseEvent):
    type = EVENT_TYPE.RESTORE

    def __init__(self, fqid: Fqid, data: Any = None) -> None:
        super().__init__(fqid, None)


EVENT_TYPE_TRANSLATION = {
    EVENT_TYPE.CREATE: CreateEvent,
    EVENT_TYPE.UPDATE: UpdateEvent,
    EVENT_TYPE.DELETE_FIELDS: DeleteFieldsEvent,
    EVENT_TYPE.LIST_FIELDS: ListUpdateEvent,
    EVENT_TYPE.DELETE: DeleteEvent,
    EVENT_TYPE.RESTORE: RestoreEvent,
}


def to_event(row: Any) -> BaseEvent:
    if row["type"] not in EVENT_TYPE_TRANSLATION:
        raise BadEventException(f"Type {row['type']} is unknown")
    return EVENT_TYPE_TRANSLATION[row["type"]](row["fqid"], row["data"])
