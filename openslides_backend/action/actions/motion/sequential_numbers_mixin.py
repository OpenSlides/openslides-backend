from ....shared.filters import FilterOperator
from ...generics.create import CreateAction


class SequentialNumbersMixin(CreateAction):
    def get_sequential_number(self, meeting_id: int) -> int:
        """
        Creates a sequential number, unique per meeting and returns it
        "datastore.max" evaluates the expressin per default with records marked as deleted
        """
        filter = FilterOperator("meeting_id", "=", meeting_id)

        number = self.datastore.max(
            collection=self.model.collection,
            filter=filter,
            field="sequential_number",
            type="int",
            lock_result=True,
        )
        number = 1 if number is None else number + 1
        return number
