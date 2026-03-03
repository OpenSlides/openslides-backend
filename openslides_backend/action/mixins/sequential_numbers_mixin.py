from collections.abc import Iterable
from typing import Any

from ...shared.interfaces.event import Event
from ...shared.patterns import fqid_from_collection_and_id
from ..action import EditFunction
from ..generics.create import CreateAction


class SequentialNumbersMixin(CreateAction):
    def create_events(self, instance: dict[str, Any]) -> Iterable[Event]:
        """
        Creates events for one instance of the current model.
        """
        events: list[Event] = list(super().create_events(instance))
        for event in events:
            event["return_fields"] = ["sequential_number"]
        yield from events

    def get_post_edit_function(self) -> EditFunction | None:
        return self.post_edit_fn

    def post_edit_fn(self, data: dict, results: dict[str, dict[str, Any]]) -> None:
        fqid = fqid_from_collection_and_id(self.model.collection, data.get("id", 0))
        data.update(results.get(fqid, {}))
