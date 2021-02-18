from ....services.datastore.deleted_models_behaviour import DeletedModelsBehaviour
from ....shared.filters import FilterOperator
from ...generics.create import CreateAction


class SequentialNumbersMixin(CreateAction):
    def get_sequential_number(self, meeting_id: int) -> int:
        """
        Creates a sequential number, unique per meeting and returns it
        """
        filter = FilterOperator("meeting_id", "=", meeting_id)

        number = self.datastore.max(
            collection=self.model.collection,
            filter=filter,
            field="sequential_number",
            get_deleted_models=DeletedModelsBehaviour.ALL_MODELS,
            lock_result=True,
        )
        number = 1 if number is None else number + 1
        return number
