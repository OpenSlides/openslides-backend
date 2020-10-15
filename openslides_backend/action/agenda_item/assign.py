from typing import Any, Dict, Iterable, List, Optional

from ...models.models import AgendaItem
from ...shared.exceptions import ActionException
from ...shared.filters import FilterOperator
from ...shared.interfaces import Event, WriteRequestElement
from ...shared.patterns import FullQualifiedId
from ...shared.schema import schema_version
from ..base import Action, ActionPayload, DataSet
from ..register import register_action


@register_action("agenda_item.assign")
class AgendaItemAssign(Action):
    """
    Action to assign agenda items.
    """

    model = AgendaItem()
    schema = {
        "$schema": schema_version,
        "title": "Agenda items assign new parent schema",
        "description": "An object containing an array of agenda item ids and the new parent id the items should be assigned to.",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "ids": {
                    "description": "An array of agenda item ids where the items should be assigned to the new parent id.",
                    "type": "array",
                    "items": {"type": "integer"},
                    "minItems": 1,
                    "uniqueItems": True,
                },
                "parent_id": {
                    "description": "The agenda item id of the new parent item.",
                    "type": ["integer", "null"],
                },
                "meeting_id": {
                    "description": "The meeting id of the aganda_items.",
                    "type": "integer",
                },
            },
            "required": ["ids", "parent_id", "meeting_id"],
        },
        "minItems": 1,
    }

    def prepare_dataset(self, payload: ActionPayload) -> DataSet:
        data = self.prepare_assign_data(
            parent_id=payload[0]["parent_id"],
            ids=payload[0]["ids"],
            meeting_id=payload[0]["meeting_id"],
        )

        return {"data": data}

    def prepare_assign_data(
        self, parent_id: Optional[int], ids: List[int], meeting_id: int
    ) -> Dict[int, Any]:
        filter = FilterOperator("meeting_id", "=", meeting_id)
        db_instances = self.database.filter(
            collection=self.model.collection,
            filter=filter,
            mapped_fields=["id"],
            lock_result=True,
        )
        data: Dict[int, Any] = {}

        if parent_id is None:
            for id_ in ids:
                if id_ not in db_instances:
                    raise ActionException(f"Id {id_} not in db_instances.")
                data[id_] = {"parent_id": None}
            return data

        # calc the ancesters of parent id
        ancesters = [parent_id]
        grandparent = self.database.get(
            FullQualifiedId(self.model.collection, parent_id), ["parent_id"]
        )
        while grandparent.get("parent_id") is not None:
            gp_parent_id = grandparent["parent_id"]
            ancesters.append(gp_parent_id)
            grandparent = self.database.get(
                FullQualifiedId(self.model.collection, gp_parent_id), ["parent_id"]
            )
        for id_ in ids:
            if id_ in ancesters:
                raise ActionException(
                    f"Assigning item {id_} to one of its children is not possible."
                )
            if id_ not in db_instances:
                raise ActionException(f"Id {id_} not in db_instances.")
            data[id_] = {"parent_id": parent_id}
        return data

    def create_write_request_elements(
        self, dataset: DataSet
    ) -> Iterable[WriteRequestElement]:
        for id, instance in dataset["data"].items():
            fqid = FullQualifiedId(self.model.collection, id)
            information = {fqid: ["Object sorted"]}
            event = Event(type="update", fqid=fqid, fields=instance)
            # TODO: Lock some fields to protect against intermediate creation of new instances but care where exactly to lock them.
            yield WriteRequestElement(
                events=[event], information=information, user_id=self.user_id
            )
