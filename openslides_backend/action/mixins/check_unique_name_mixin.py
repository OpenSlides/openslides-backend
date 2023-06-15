from openslides_backend.action.action import Action
from openslides_backend.shared.exceptions import ActionException
from openslides_backend.shared.filters import And, FilterOperator


class CheckUniqueInContextMixin(Action):
    def check_unique_in_context(
        self,
        unique_name: str,
        unique_value: str,
        exception_message: str,
        context_name: str = "",
        context_id: int = 0,
    ) -> None:
        """
        checks uniqueness of a string_value in context, i.e. in meeting, committee or organisation
        Leave context_name empty to look without context
        """
        if context_name:
            name_exists = self.datastore.exists(
                self.model.collection,
                And(
                    FilterOperator(unique_name, "=", unique_value),
                    FilterOperator(context_name, "=", context_id),
                ),
            )
        else:
            name_exists = self.datastore.exists(
                self.model.collection,
                FilterOperator(unique_name, "=", unique_value),
            )

        if name_exists:
            raise ActionException(exception_message)
