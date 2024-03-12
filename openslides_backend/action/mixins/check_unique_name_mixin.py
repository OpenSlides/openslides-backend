from openslides_backend.action.action import Action
from openslides_backend.shared.exceptions import ActionException
from openslides_backend.shared.filters import And, Filter, FilterOperator


class CheckUniqueInContextMixin(Action):
    def check_unique_in_context(
        self,
        unique_name: str,
        unique_value: str,
        exception_message: str,
        self_id: int | None = None,
        context_name: str = "",
        context_id: int = 0,
    ) -> None:
        """
        checks uniqueness of a string_value in context, i.e. in meeting, committee or organisation
        Leave context_name empty to look without context. On case of update put the id of your object
        to self_id to exclude the object itself from search.
        """
        filter: Filter = FilterOperator(unique_name, "=", unique_value)
        if context_name:
            filter = And(
                filter,
                FilterOperator(context_name, "=", context_id),
            )
        if self_id:
            filter = And(filter, FilterOperator("id", "!=", self_id))

        name_exists = self.datastore.exists(
            self.model.collection,
            filter,
        )

        if name_exists:
            raise ActionException(exception_message)
