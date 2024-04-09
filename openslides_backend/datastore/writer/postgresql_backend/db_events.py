from typing import Any

from openslides_backend.datastore.shared.postgresql_backend import (
    EVENT_TYPE,
    ListUpdatesDict,
    apply_fields,
)
from openslides_backend.datastore.shared.typing import JSON, Fqid, Model
from openslides_backend.datastore.shared.util import (
    META_DELETED,
    BadCodingError,
    InvalidFormat,
)


class BaseDbEvent:
    event_type: EVENT_TYPE

    def __init__(self, fqid: str) -> None:
        self.fqid = fqid

    def get_modified_fields(self) -> dict[str, JSON]:
        raise NotImplementedError()

    def get_event_data(self) -> Any:
        raise NotImplementedError()


class BaseDbEventWithValues(BaseDbEvent):
    def __init__(self, fqid: str, field_data: dict[str, JSON]) -> None:
        super().__init__(fqid)
        self.field_data = field_data

    def get_modified_fields(self) -> dict[str, JSON]:
        return self.field_data

    def get_event_data(self) -> Any:
        return self.field_data


class BaseDbEventWithoutValues(BaseDbEvent):
    def __init__(self, fqid: str, fields: list[str]) -> None:
        super().__init__(fqid)
        self.fields = fields

    def get_modified_fields(self) -> dict[str, JSON]:
        return {field: None for field in self.fields}


class DeletionStateChangeMixin(BaseDbEvent):
    def get_modified_fields(self) -> dict[str, JSON]:
        return {
            **super().get_modified_fields(),
            META_DELETED: self.event_type == EVENT_TYPE.DELETE,
        }


class DbCreateEvent(DeletionStateChangeMixin, BaseDbEventWithValues):
    event_type = EVENT_TYPE.CREATE


class DbUpdateEvent(BaseDbEventWithValues):
    event_type = EVENT_TYPE.UPDATE


class DbListUpdateEvent(BaseDbEvent):
    event_type = EVENT_TYPE.LIST_FIELDS

    def __init__(
        self, fqid: str, add: ListUpdatesDict, remove: ListUpdatesDict, model: Model
    ) -> None:
        super().__init__(fqid)
        self.add = add
        self.remove = remove

        self.modified_fields = self.calculate_modified_fields(model)

    def calculate_modified_fields(self, model: Model) -> dict[str, JSON]:
        all_field_keys = list(self.add.keys()) + list(self.remove.keys())
        for field in all_field_keys:
            db_list = model.get(field, [])
            if not isinstance(db_list, list):
                raise InvalidFormat(
                    f"Field {field} on model {self.fqid} is not a list, but of type"
                    + str(type(db_list))
                )
            for el in db_list:
                if not isinstance(el, (str, int)):
                    raise InvalidFormat(
                        f"Field {field} on model {self.fqid} contains invalid entry "
                        f"for list update (of type {type(el)}): {el}"
                    )

        return apply_fields(model, self.add, self.remove)

    def get_modified_fields(self) -> dict[str, JSON]:
        return self.modified_fields

    def get_event_data(self) -> Any:
        return {"add": self.add, "remove": self.remove}


class DbDeleteFieldsEvent(BaseDbEventWithoutValues):
    event_type = EVENT_TYPE.DELETE_FIELDS

    def get_event_data(self) -> Any:
        return self.fields


class DbDeleteEvent(BaseDbEventWithoutValues, DeletionStateChangeMixin):
    event_type = EVENT_TYPE.DELETE

    def get_event_data(self) -> Any:
        return None


class DbRestoreEvent(BaseDbEventWithoutValues, DeletionStateChangeMixin):
    event_type = EVENT_TYPE.RESTORE

    def get_event_data(self) -> Any:
        return None


def apply_event_to_models(event: BaseDbEvent, models: dict[Fqid, Model]) -> None:
    """Utility function to apply an event to a model dict."""
    if isinstance(event, DbCreateEvent):
        models[event.fqid] = {**event.field_data, META_DELETED: False}
    elif isinstance(event, (DbUpdateEvent, DbListUpdateEvent)):
        models[event.fqid].update(event.get_modified_fields())
    elif isinstance(event, DbDeleteFieldsEvent):
        for field in event.fields:
            if field in models[event.fqid]:
                del models[event.fqid][field]
    elif isinstance(event, (DbDeleteEvent, DbRestoreEvent)):
        models[event.fqid][META_DELETED] = isinstance(event, DbDeleteEvent)
    else:
        raise BadCodingError()
