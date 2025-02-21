from collections.abc import Iterable
from typing import Any

from openslides_backend.models.fields import GenericRelationField, RelationField
from openslides_backend.shared.interfaces.event import Event, EventType
from openslides_backend.shared.patterns import fqid_from_collection_and_id, id_from_fqid

from ..action import Action


class ExtendHistoryMixin(Action):
    """
    Dynamic mixin class to extend the history of some related object with the entry of this one.
    Adds a dummy event with an update to the model's id to the event list.
    """

    extend_history_to: str

    def create_events(self, instance: dict[str, Any]) -> Iterable[Event]:
        yield from super().create_events(instance)
        field = self.model.get_field(self.extend_history_to)
        model = self.datastore.get(
            fqid_from_collection_and_id(self.model.collection, instance["id"]),
            [self.extend_history_to],
        )
        value = model[self.extend_history_to]
        if isinstance(field, GenericRelationField):
            yield self.build_event(EventType.Update, value, {"id": id_from_fqid(value)})
        elif isinstance(field, RelationField):
            yield self.build_event(
                EventType.Update,
                fqid_from_collection_and_id(field.get_target_collection(), value),
                {"id": value},
            )
        else:
            raise TypeError(f"Invalid related field type: {type(field)}")
