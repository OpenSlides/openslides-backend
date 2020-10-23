from typing import Any, Dict, Iterable, List, Optional

from ...models.models import AgendaItem
from ...shared.exceptions import ActionException
from ...shared.filters import FilterOperator
from ...shared.patterns import FullQualifiedId
from ...shared.schema import id_list_schema
from ..base import ActionPayload
from ..default_schema import DefaultSchema
from ..generics import UpdateAction
from ..register import register_action


@register_action("agenda_item.assign")
class AgendaItemAssign(UpdateAction):
    """
    Action to assign agenda items.
    """

    model = AgendaItem()
    schema = DefaultSchema(AgendaItem()).get_default_schema(
        title="Agenda items assign new parent schema",
        description="An object containing an array of agenda item ids and the new parent id the items should be assigned to.",
        required_properties=["parent_id", "meeting_id"],
        additional_required_fields={
            "ids": {
                "description": "An array of agenda item ids where the items should be assigned to the new parent id.",
                **id_list_schema,
            }
        },
        single_item=True,
    )

    def get_updated_instances(self, payload: ActionPayload) -> Iterable[Dict[str, Any]]:
        return self.prepare_assign_data(
            parent_id=payload[0]["parent_id"],
            ids=payload[0]["ids"],
            meeting_id=payload[0]["meeting_id"],
        )

    def prepare_assign_data(
        self, parent_id: Optional[int], ids: List[int], meeting_id: int
    ) -> Iterable[Dict[str, Any]]:
        filter = FilterOperator("meeting_id", "=", meeting_id)
        db_instances = self.database.filter(
            collection=self.model.collection,
            filter=filter,
            mapped_fields=["id"],
            lock_result=True,
        )

        if parent_id is None:
            for id_ in ids:
                if id_ not in db_instances:
                    raise ActionException(f"Id {id_} not in db_instances.")
                yield {"id": id_, "parent_id": None}
        else:
            # Calculate the ancesters of parent
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
                yield {"id": id_, "parent_id": parent_id}
