from typing import Any

from ...models.models import Model
from ...services.database.interface import Database
from ...shared.filters import FilterOperator
from ..generics.create import CreateAction
from ..util.typing import ActionResultElement


class SequentialNumbersMixin(CreateAction):
    datastore: Database
    model: Model

    def get_sequential_number(self, meeting_id: int) -> int:
        """
        Creates a sequential number, unique per meeting and returns it
        """
        filter = FilterOperator("meeting_id", "=", meeting_id)

        number = self.datastore.max(
            collection=self.model.collection,
            filter_=filter,
            field="sequential_number",
        )
        number = 1 if number is None else number + 1
        return number

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        instance = super().update_instance(instance)
        instance["sequential_number"] = self.get_sequential_number(
            instance["meeting_id"]
        )
        return instance

    def create_action_result_element(
        self, instance: dict[str, Any]
    ) -> ActionResultElement | None:
        result = super().create_action_result_element(instance)
        if result is None:
            result = {"id": instance["id"]}
        result["sequential_number"] = instance["sequential_number"]
        return result
