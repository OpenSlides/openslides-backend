from ...shared.exceptions import ActionException
from ...shared.filters import Filter
from ..action import Action
from ..util.typing import ActionData


class LinearSortMixin(Action):
    """
    Provides a mixin for linear sorting.
    """

    def sort_linear(
        self,
        nodes: list,
        filter: Filter,
        weight_key: str = "weight",
    ) -> ActionData:
        db_instances = self.datastore.filter(
            collection=self.model.collection,
            filter=filter,
            mapped_fields=["id"],
        )
        valid_instance_ids = []
        for id_ in nodes:
            if id_ not in db_instances:
                raise ActionException(
                    f"{self.model.collection} sorting failed, because element {self.model.collection}/{id_} doesn't exist."
                )
            valid_instance_ids.append(id_)
        if len(valid_instance_ids) != len(db_instances):
            raise ActionException(
                f"{self.model.collection} sorting failed, because some elements were not included in the call."
            )

        weight = 1
        for id_ in valid_instance_ids:
            yield {"id": id_, weight_key: weight}
            weight += 1
