from typing import List, Optional

from ...shared.exceptions import ActionException
from ...shared.filters import Filter, FilterOperator
from ..action import BaseAction
from ..util.typing import ActionPayload


class LinearSortMixin(BaseAction):
    """
    Provides a mixin for linear sorting.
    """

    def sort_linear(
        self,
        nodes: List,
        filter_id: int,
        filter_str: str,
        weight_key: str = "weight",
        filter: Optional[Filter] = None,
    ) -> ActionPayload:
        if not filter:
            filter = FilterOperator(filter_str, "=", filter_id)
        db_instances = self.datastore.filter(
            collection=self.model.collection,
            filter=filter,
            mapped_fields=["id"],
            lock_result=True,
        )
        valid_instance_ids = []
        for id_ in nodes:
            if id_ not in db_instances:
                raise ActionException(f"Id {id_} not in db_instances.")
            valid_instance_ids.append(id_)
        if len(valid_instance_ids) != len(db_instances):
            raise ActionException("Additional db_instances found.")

        weight = 1
        for id_ in valid_instance_ids:
            yield {"id": id_, weight_key: weight}
            weight += 1
