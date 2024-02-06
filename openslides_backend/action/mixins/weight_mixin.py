from ...shared.filters import Filter, FilterOperator
from ...shared.patterns import Collection
from ..action import Action


class WeightMixin(Action):
    def get_weight(
        self, filter: int | Filter, collection: Collection | None = None
    ) -> int:
        """
        Returns the current maximum weight + 1.
        """
        if not collection:
            collection = self.model.collection
        if isinstance(filter, int):
            filter = FilterOperator("meeting_id", "=", filter)
        weight = self.datastore.max(collection, filter, "weight")
        return (weight or 0) + 1
